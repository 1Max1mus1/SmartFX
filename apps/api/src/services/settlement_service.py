from __future__ import annotations

from datetime import date, timedelta

from src.clients.kimi_client import DISCLAIMER, KimiClient
from src.schemas.format import ResponseFormatter
from src.schemas.settlement import SettlementAnalysisPayload, SettlementRequest
from src.services.rate_service import RateService

RESPONSE = ResponseFormatter(prefix="[SettlementService]")


def _normalize_currency(code: str) -> str:
    normalized = code.upper()
    if normalized not in {"USD", "HKD", "CNY"}:
        raise ValueError(f"unsupported currency: {code}")
    return normalized


def _zone_label(percentile: float) -> str:
    if percentile <= 35:
        return "低位"
    if percentile >= 65:
        return "高位"
    return "中位"


def _pair_for_stats(source_currency: str, target_currency: str) -> str:
    pair = f"{source_currency}/{target_currency}"
    if pair in {"USD/CNY", "HKD/CNY", "USD/HKD"}:
        return pair
    if pair == "CNY/USD":
        return "USD/CNY"
    if pair == "CNY/HKD":
        return "HKD/CNY"
    if pair == "HKD/USD":
        return "USD/HKD"
    return "USD/CNY"


def _projected_best_case_value(
    request: SettlementRequest,
    immediate_value: float,
    percentile_30d: float,
    change_pct_7d: float,
) -> float:
    if request.target_rate:
        return round(request.amount * request.target_rate, 2)

    opportunity_factor = (
        max(0.0, (100 - percentile_30d) / 100)
        if request.optimization_goal == "maximize_income"
        else max(0.0, percentile_30d / 100)
    )
    short_term_factor = min(0.012, abs(change_pct_7d) / 100)
    uplift = 0.010 + (0.012 * opportunity_factor) + short_term_factor
    if request.optimization_goal == "minimize_cost":
        uplift = 0.006 + (0.010 * opportunity_factor) + (short_term_factor / 2)
    return round(immediate_value * (1 + uplift), 2)


class SettlementService:
    @staticmethod
    async def analyze(request: SettlementRequest) -> tuple[dict, object]:
        try:
            source_currency = _normalize_currency(request.source_currency)
            target_currency = _normalize_currency(request.target_currency)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        try:
            current_rate = await RateService.get_live_conversion_rate(source_currency, target_currency)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        stats_pair = _pair_for_stats(source_currency, target_currency)
        stats_7d, response_7d = await RateService.get_stats(stats_pair, 7)
        if response_7d.status_code >= 300:
            return {}, response_7d

        stats_30d, response_30d = await RateService.get_stats(stats_pair, 30)
        if response_30d.status_code >= 300:
            return {}, response_30d

        stats_90d, response_90d = await RateService.get_stats(stats_pair, 90)
        if response_90d.status_code >= 300:
            return {}, response_90d

        immediate_value = round(request.amount * current_rate, 2)
        percentile_30d = stats_30d["percentile"]
        percentile_90d = stats_90d["percentile"]
        projected_best_case_value = _projected_best_case_value(
            request,
            immediate_value,
            percentile_30d,
            stats_7d["change_pct_24h"],
        )
        estimated_delta = round(projected_best_case_value - immediate_value, 2)
        zone_label = _zone_label(percentile_90d)

        base_analysis = {
            "pair": f"{source_currency}/{target_currency}",
            "current_rate": current_rate,
            "current_percentile_30d": percentile_30d,
            "current_percentile_90d": percentile_90d,
            "immediate_value": immediate_value,
            "projected_best_case_value": projected_best_case_value,
            "estimated_delta": estimated_delta,
            "zone_label": zone_label,
        }
        market_context = {
            "stats_7d": stats_7d,
            "stats_30d": stats_30d,
            "stats_90d": stats_90d,
            "arrival_date": request.arrival_date.isoformat(),
            "latest_settlement_date": request.latest_settlement_date.isoformat() if request.latest_settlement_date else None,
        }
        window_suggestion = await KimiClient().recommend_settlement_window(
            base_analysis,
            request.model_dump(mode="json"),
            market_context,
        )

        recommended_window_days = int(window_suggestion["recommended_window_days"])
        recommended_window_end_date = min(
            request.arrival_date,
            date.today() + timedelta(days=recommended_window_days),
        )
        recommended_window_reason = window_suggestion["recommended_window_reason"]

        narrative = (
            f"当前 {base_analysis['pair']} 约处于近 30 天 {percentile_30d:.2f}% 和近 90 天 "
            f"{percentile_90d:.2f}% 的区间位置。若立即结算，参考价值约为 {immediate_value:.2f} "
            f"{target_currency}；若等待更优窗口，参考值约为 {projected_best_case_value:.2f} {target_currency}，"
            f"两者差额约为 {estimated_delta:.2f} {target_currency}。建议先观察 {recommended_window_days} 天，"
            f"观察至 {recommended_window_end_date.isoformat()}，重点关注 {recommended_window_reason}"
        )

        payload = SettlementAnalysisPayload(
            pair=base_analysis["pair"],
            current_rate=current_rate,
            current_percentile_30d=percentile_30d,
            current_percentile_90d=percentile_90d,
            immediate_value=immediate_value,
            projected_best_case_value=projected_best_case_value,
            estimated_delta=estimated_delta,
            recommended_window_days=recommended_window_days,
            recommended_window_end_date=recommended_window_end_date,
            recommended_window_reason=recommended_window_reason,
            zone_label=zone_label,
            narrative=narrative,
            disclaimer=DISCLAIMER,
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("settlement analysis ready")
