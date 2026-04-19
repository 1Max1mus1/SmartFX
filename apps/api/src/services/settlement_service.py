from __future__ import annotations

from src.clients.kimi_client import DISCLAIMER
from src.schemas.format import ResponseFormatter
from src.schemas.settlement import SettlementAnalysisPayload, SettlementRequest
from src.services.rate_service import RateService, get_conversion_rate

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


def _recommended_window_days(percentile_30d: float, optimization_goal: str) -> int:
    if optimization_goal == "maximize_income":
        if percentile_30d >= 65:
            return 3
        if percentile_30d <= 35:
            return 10
        return 5
    if percentile_30d <= 35:
        return 2
    return 6


class SettlementService:
    @staticmethod
    async def analyze(request: SettlementRequest) -> tuple[dict, object]:
        try:
            source_currency = _normalize_currency(request.source_currency)
            target_currency = _normalize_currency(request.target_currency)
            pair = f"{source_currency}/{target_currency}"
            current_rate = get_conversion_rate(source_currency, target_currency)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        stats_pair = pair if pair in {"USD/CNY", "HKD/CNY", "USD/HKD"} else "USD/CNY"
        stats_30d, response_30d = await RateService.get_stats(stats_pair, 30)
        if response_30d.status_code >= 300:
            return {}, response_30d

        stats_90d, response_90d = await RateService.get_stats(stats_pair, 90)
        if response_90d.status_code >= 300:
            return {}, response_90d

        immediate_value = round(request.amount * current_rate, 2)
        percentile_30d = stats_30d["percentile"]
        percentile_90d = stats_90d["percentile"]

        opportunity_factor = (
            max(0.0, (100 - percentile_30d) / 100)
            if request.optimization_goal == "maximize_income"
            else max(0.0, percentile_30d / 100)
        )
        projected_best_case_value = round(immediate_value * (1 + (0.018 * opportunity_factor)), 2)

        if request.target_rate:
            projected_best_case_value = round(request.amount * request.target_rate, 2)

        estimated_delta = round(projected_best_case_value - immediate_value, 2)
        window_days = _recommended_window_days(percentile_30d, request.optimization_goal)
        zone_label = _zone_label(percentile_90d)

        narrative = (
            f"当前 {pair} 约处于近 30 天 {round(percentile_30d, 2)}% 和近 90 天 {round(percentile_90d, 2)}% 的区间位置。"
            f"如果立即结算，参考价值约为 {immediate_value:.2f} {target_currency}；"
            f"如果等待更优窗口，历史区间推演下的最佳参考值约为 {projected_best_case_value:.2f} {target_currency}，"
            f"两者差额约为 {estimated_delta:.2f} {target_currency}。"
            f"更适合在未来 {window_days} 天内持续观察，并结合到账节奏安排执行。"
        )

        payload = SettlementAnalysisPayload(
            pair=pair,
            current_rate=current_rate,
            current_percentile_30d=percentile_30d,
            current_percentile_90d=percentile_90d,
            immediate_value=immediate_value,
            projected_best_case_value=projected_best_case_value,
            estimated_delta=estimated_delta,
            recommended_window_days=window_days,
            zone_label=zone_label,
            narrative=narrative,
            disclaimer=DISCLAIMER,
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("settlement analysis ready")
