from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from src.clients.kimi_client import DISCLAIMER, KimiClient
from src.schemas.format import ResponseFormatter
from src.schemas.student_payment import (
    StudentPaymentAdvicePayload,
    StudentPaymentAdviceRequest,
    StudentPaymentMarketSnapshotPayload,
)
from src.services.rate_service import RateService

RESPONSE = ResponseFormatter(prefix="[StudentPaymentAdviceService]")
SUPPORTED_CURRENCIES = {"USD", "HKD", "CNY"}
SUPPORTED_PAIRS = {"USD/CNY", "HKD/CNY", "USD/HKD"}


@dataclass
class DirectionalStats:
    requested_pair: str
    reference_pair: str
    current_rate: float
    reference_rate: float
    change_pct_24h: float
    percentile_30d: float
    percentile_90d: float
    favorable_score_30d: float
    favorable_score_90d: float


def _normalize_currency(code: str) -> str:
    normalized = code.upper()
    if normalized not in SUPPORTED_CURRENCIES:
        raise ValueError(f"unsupported currency: {code}")
    return normalized


def _resolve_reference_pair(source_currency: str, target_currency: str) -> tuple[str, bool]:
    requested_pair = f"{source_currency}/{target_currency}"
    if requested_pair in SUPPORTED_PAIRS:
        return requested_pair, False

    inverse_pair = f"{target_currency}/{source_currency}"
    if inverse_pair in SUPPORTED_PAIRS:
        return inverse_pair, True

    raise ValueError(f"unsupported conversion pair: {requested_pair}")


def _percentile(current: float, values: list[float]) -> float:
    if not values:
        return 0.0
    below = sum(1 for value in values if value <= current)
    return round((below / len(values)) * 100, 2)


def _assessment_from_percentile(percentile: float) -> str:
    if percentile <= 20:
        return "偏低"
    if percentile <= 40:
        return "较低"
    if percentile <= 70:
        return "中位"
    return "偏高"


def _pressure_from_days(days_to_deadline: int) -> str:
    if days_to_deadline <= 2:
        return "高"
    if days_to_deadline <= 7:
        return "中"
    return "低"


def _favorable_label(score: float) -> str:
    if score >= 80:
        return "较优"
    if score >= 60:
        return "尚可"
    if score >= 40:
        return "中性"
    return "不占优"


def _watch_window_days(days_to_deadline: int, risk_preference: str) -> int:
    max_window = max(1, min(3, days_to_deadline - 1))
    if risk_preference == "stable":
        return 1
    if risk_preference == "balanced":
        return min(2, max_window)
    return max_window


def _split_ratio(deadline_pressure: str, risk_preference: str, favorable_score_30d: float) -> int:
    if deadline_pressure == "高" or risk_preference == "stable":
        return 80
    if favorable_score_30d >= 75:
        return 70
    if deadline_pressure == "中":
        return 70
    if risk_preference == "opportunistic":
        return 50
    return 60


class StudentPaymentAdviceService:
    @staticmethod
    async def analyze(request: StudentPaymentAdviceRequest) -> tuple[dict, object]:
        try:
            source_currency = _normalize_currency(request.source_currency)
            target_currency = _normalize_currency(request.target_currency)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        if source_currency == target_currency:
            return {}, RESPONSE.error(400, "source_currency and target_currency must be different")

        days_to_deadline = (request.deadline_date - date.today()).days
        if days_to_deadline < 0:
            return {}, RESPONSE.error(400, "deadline_date must be today or later")

        try:
            stats = await StudentPaymentAdviceService._build_directional_stats(source_currency, target_currency)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        deadline_pressure = _pressure_from_days(days_to_deadline)
        rate_assessment = _assessment_from_percentile(stats.percentile_30d)

        decision_level = StudentPaymentAdviceService._decision_level(
            days_to_deadline=days_to_deadline,
            favorable_score_30d=stats.favorable_score_30d,
            can_split_payment=request.can_split_payment,
            risk_preference=request.risk_preference,
        )
        decision, suggested_action, split_payment_plan = StudentPaymentAdviceService._build_actions(
            request=request,
            stats=stats,
            deadline_pressure=deadline_pressure,
            decision_level=decision_level,
            days_to_deadline=days_to_deadline,
        )
        decision_reason = StudentPaymentAdviceService._build_reason(
            request=request,
            stats=stats,
            deadline_pressure=deadline_pressure,
            rate_assessment=rate_assessment,
        )
        analysis_markdown = StudentPaymentAdviceService._build_markdown(
            request=request,
            stats=stats,
            deadline_pressure=deadline_pressure,
            rate_assessment=rate_assessment,
            decision=decision,
            decision_reason=decision_reason,
            suggested_action=suggested_action,
            split_payment_plan=split_payment_plan,
        )
        analysis_markdown = await KimiClient().generate_student_payment_advice(
            request=request.model_dump(mode="json"),
            advice_context={
                "decision": decision,
                "decision_level": decision_level,
                "decision_reason": decision_reason,
                "rate_assessment": rate_assessment,
                "deadline_pressure": deadline_pressure,
                "suggested_action": suggested_action,
                "split_payment_plan": split_payment_plan,
                "market_snapshot": {
                    "requested_pair": stats.requested_pair,
                    "reference_pair": stats.reference_pair,
                    "current_rate": stats.current_rate,
                    "reference_rate": stats.reference_rate,
                    "change_pct_24h": stats.change_pct_24h,
                    "percentile_30d": stats.percentile_30d,
                    "percentile_90d": stats.percentile_90d,
                    "favorable_score_30d": stats.favorable_score_30d,
                    "favorable_score_90d": stats.favorable_score_90d,
                },
            },
            fallback_markdown=analysis_markdown,
        )

        payload = StudentPaymentAdvicePayload(
            decision=decision,
            decision_level=decision_level,
            decision_reason=decision_reason,
            rate_assessment=rate_assessment,
            deadline_pressure=deadline_pressure,
            suggested_action=suggested_action,
            split_payment_plan=split_payment_plan,
            market_snapshot=StudentPaymentMarketSnapshotPayload(
                requested_pair=stats.requested_pair,
                reference_pair=stats.reference_pair,
                current_rate=stats.current_rate,
                reference_rate=stats.reference_rate,
                change_pct_24h=stats.change_pct_24h,
                percentile_30d=stats.percentile_30d,
                percentile_90d=stats.percentile_90d,
                favorable_score_30d=stats.favorable_score_30d,
                favorable_score_90d=stats.favorable_score_90d,
            ),
            analysis_markdown=analysis_markdown,
            disclaimer=DISCLAIMER,
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("student payment advice ready")

    @staticmethod
    async def _build_directional_stats(source_currency: str, target_currency: str) -> DirectionalStats:
        reference_pair, is_inverse = _resolve_reference_pair(source_currency, target_currency)
        requested_pair = f"{source_currency}/{target_currency}"
        current_rate = await RateService.get_live_conversion_rate(source_currency, target_currency)

        history_30d_payload, response_30d = await RateService.get_history(reference_pair, 30)
        if response_30d.status_code >= 300:
            raise ValueError(response_30d.detail)

        history_90d_payload, response_90d = await RateService.get_history(reference_pair, 90)
        if response_90d.status_code >= 300:
            raise ValueError(response_90d.detail)

        rates_30d = StudentPaymentAdviceService._directional_rates(
            history_30d_payload["points"],
            current_rate=current_rate,
            is_inverse=is_inverse,
        )
        rates_90d = StudentPaymentAdviceService._directional_rates(
            history_90d_payload["points"],
            current_rate=current_rate,
            is_inverse=is_inverse,
        )

        reference_rate = round((1 / current_rate), 6) if is_inverse else current_rate
        percentile_30d = _percentile(current_rate, rates_30d)
        percentile_90d = _percentile(current_rate, rates_90d)
        favorable_score_30d = percentile_30d
        favorable_score_90d = percentile_90d
        previous_rate = rates_30d[-2] if len(rates_30d) >= 2 else current_rate
        change_pct_24h = round(((current_rate - previous_rate) / previous_rate) * 100, 4) if previous_rate else 0.0

        return DirectionalStats(
            requested_pair=requested_pair,
            reference_pair=reference_pair,
            current_rate=current_rate,
            reference_rate=reference_rate,
            change_pct_24h=change_pct_24h,
            percentile_30d=percentile_30d,
            percentile_90d=percentile_90d,
            favorable_score_30d=favorable_score_30d,
            favorable_score_90d=favorable_score_90d,
        )

    @staticmethod
    def _directional_rates(points: list[dict], *, current_rate: float, is_inverse: bool) -> list[float]:
        rates = [round((1 / point["rate"]), 6) if is_inverse else round(float(point["rate"]), 6) for point in points]
        if not rates:
            return [current_rate]
        rates[-1] = current_rate
        return rates

    @staticmethod
    def _decision_level(
        *,
        days_to_deadline: int,
        favorable_score_30d: float,
        can_split_payment: bool,
        risk_preference: str,
    ) -> str:
        if days_to_deadline <= 2:
            return "pay_now"

        if risk_preference == "stable":
            if favorable_score_30d >= 55 or days_to_deadline <= 7:
                return "pay_now"
            return "watch_short"

        if favorable_score_30d >= 80:
            if can_split_payment and risk_preference == "opportunistic" and days_to_deadline > 5:
                return "split_now"
            return "pay_now"

        if days_to_deadline <= 7:
            if can_split_payment and favorable_score_30d >= 45:
                return "split_now"
            return "pay_now"

        if can_split_payment and favorable_score_30d >= 40:
            return "split_now"

        return "watch_short"

    @staticmethod
    def _build_actions(
        *,
        request: StudentPaymentAdviceRequest,
        stats: DirectionalStats,
        deadline_pressure: str,
        decision_level: str,
        days_to_deadline: int,
    ) -> tuple[str, str, str | None]:
        if decision_level == "pay_now":
            decision = "建议今天完成支付"
            action = "优先锁定本次缴费所需金额，避免因截止日临近或短期波动影响安排。"
            if request.amount:
                action = (
                    f"优先锁定本次约 {request.amount:.2f} {request.source_currency.upper()} 对应的支付金额，"
                    "避免因截止日临近或短期波动影响安排。"
                )
            return decision, action, None

        if decision_level == "split_now":
            first_ratio = _split_ratio(deadline_pressure, request.risk_preference, stats.favorable_score_30d)
            remaining_ratio = 100 - first_ratio
            watch_days = _watch_window_days(days_to_deadline, request.risk_preference)
            watch_end_date = min(request.deadline_date, date.today() + timedelta(days=watch_days))
            decision = f"建议先支付 {first_ratio}%，剩余部分短观察后完成"
            action = f"今天先锁定大部分金额，剩余部分在 {watch_days} 天内根据汇率变化补齐。"
            split_plan = (
                f"{first_ratio}% 今天支付，{remaining_ratio}% 最晚于 {watch_end_date.isoformat()} 前完成。"
            )
            return decision, action, split_plan

        watch_days = _watch_window_days(days_to_deadline, request.risk_preference)
        watch_end_date = min(request.deadline_date, date.today() + timedelta(days=watch_days))
        decision = f"建议先观察 {watch_days} 天，再决定是否支付"
        action = (
            f"当前可继续短观察，但建议把执行窗口控制在 {watch_end_date.isoformat()} 之前，"
            "不要为了等更低点位而压缩实际支付时间。"
        )
        return decision, action, None

    @staticmethod
    def _build_reason(
        *,
        request: StudentPaymentAdviceRequest,
        stats: DirectionalStats,
        deadline_pressure: str,
        rate_assessment: str,
    ) -> str:
        favorable_label = _favorable_label(stats.favorable_score_30d)
        pair_context = (
            f"当前 {stats.requested_pair} 对你这笔支付的 30 天相对位置为 {stats.percentile_30d:.2f}%"
        )
        if deadline_pressure == "高":
            return f"{pair_context}，且截止时间较近，应优先保证按时完成支付。"
        return (
            f"{pair_context}，参考牌价处于近 30 天{rate_assessment}区间，"
            f"从本次支付角度看属于{favorable_label}位置。"
        )

    @staticmethod
    def _build_markdown(
        *,
        request: StudentPaymentAdviceRequest,
        stats: DirectionalStats,
        deadline_pressure: str,
        rate_assessment: str,
        decision: str,
        decision_reason: str,
        suggested_action: str,
        split_payment_plan: str | None,
    ) -> str:
        lines = [
            "## 今日建议",
            "",
            decision,
            "",
            "## 判断依据",
            "",
            f"- 请求方向：{stats.requested_pair}",
            f"- 参考牌价：{stats.reference_pair} = {stats.reference_rate:.6f}",
            f"- 当前成交方向汇率：{stats.current_rate:.6f}",
            f"- 近 24 小时变化：{stats.change_pct_24h:.4f}%",
            f"- 近 30 天位置：{stats.percentile_30d:.2f}%",
            f"- 近 90 天位置：{stats.percentile_90d:.2f}%",
            f"- 参考牌价判断：{rate_assessment}",
            f"- 截止日压力：{deadline_pressure}",
            "",
            "## 解释",
            "",
            decision_reason,
            "",
            "## 操作建议",
            "",
            f"- {suggested_action}",
        ]
        if split_payment_plan:
            lines.extend(["- " + split_payment_plan])
        if request.notes:
            lines.extend(["", "## 备注考虑", "", f"- 已参考你的补充信息：{request.notes}"])
        lines.extend(["", DISCLAIMER])
        return "\n".join(lines)
