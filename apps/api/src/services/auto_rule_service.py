from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.kimi_client import DISCLAIMER
from src.models.alert_history import AlertHistory
from src.models.auto_decision_rule import AutoDecisionRule
from src.models.user import User
from src.repositories.auto_rule_repository import AutoRuleRepository
from src.schemas.auto_rules import (
    AlertHistoryListPayload,
    AlertHistoryPayload,
    AutoRuleCreateRequest,
    AutoRuleListPayload,
    AutoRulePayload,
    AutoRuleUpdateRequest,
)
from src.schemas.format import ResponseFormatter
from src.services.daily_report_service import DailyReportService
from src.services.rate_service import RateService, SUPPORTED_PAIRS

RESPONSE = ResponseFormatter(prefix="[AutoRuleService]")
LOCAL_TZ = timezone(timedelta(hours=8))
PAIR_SIGNAL_FIELD = {
    "USD/CNY": "signal_usd_cny",
    "HKD/CNY": "signal_hkd_cny",
    "USD/HKD": "signal_usd_hkd",
}


def _now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def _serialize_rule(rule: AutoDecisionRule) -> AutoRulePayload:
    return AutoRulePayload(
        id=rule.id,
        pair=rule.pair,
        trigger_mode=rule.trigger_mode,
        rate_condition=rule.rate_condition,
        target_rate=rule.target_rate,
        signal_condition=rule.signal_condition,
        watch_amount=rule.watch_amount,
        quiet_hours_start=rule.quiet_hours_start,
        quiet_hours_end=rule.quiet_hours_end,
        cooldown_minutes=rule.cooldown_minutes,
        notes=rule.notes,
        is_active=rule.is_active,
        last_triggered_at=rule.last_triggered_at,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _serialize_history(item: AlertHistory) -> AlertHistoryPayload:
    return AlertHistoryPayload(
        id=item.id,
        rule_id=item.rule_id,
        pair=item.pair,
        trigger_mode=item.trigger_mode,
        evaluated_value=item.evaluated_value,
        signal_value=item.signal_value,
        message=item.message,
        notification_channel=item.notification_channel,
        delivery_status=item.delivery_status,
        created_at=item.created_at,
    )


def _validate_pair(pair: str) -> str:
    normalized = pair.upper()
    if normalized not in SUPPORTED_PAIRS:
        raise ValueError(f"unsupported pair: {pair}")
    return normalized


def _merged_rule_payload(rule: AutoDecisionRule, updates: AutoRuleUpdateRequest) -> AutoRuleCreateRequest:
    base = {
        "pair": rule.pair,
        "trigger_mode": rule.trigger_mode,
        "rate_condition": rule.rate_condition,
        "target_rate": rule.target_rate,
        "signal_condition": rule.signal_condition,
        "watch_amount": rule.watch_amount,
        "quiet_hours_start": rule.quiet_hours_start,
        "quiet_hours_end": rule.quiet_hours_end,
        "cooldown_minutes": rule.cooldown_minutes,
        "notes": rule.notes,
        "is_active": rule.is_active,
    }
    base.update(updates.model_dump(exclude_unset=True))
    return AutoRuleCreateRequest.model_validate(base)


def _is_in_quiet_hours(rule: AutoDecisionRule, current_time: datetime) -> bool:
    if rule.quiet_hours_start is None or rule.quiet_hours_end is None:
        return False
    hour = current_time.hour
    start = rule.quiet_hours_start
    end = rule.quiet_hours_end
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def _is_rate_triggered(rule: AutoDecisionRule, current_rate: float) -> bool:
    if rule.rate_condition == "above":
        return current_rate >= float(rule.target_rate or 0)
    return current_rate <= float(rule.target_rate or 0)


class AutoRuleService:
    @staticmethod
    async def list_rules(session: AsyncSession, user: User) -> tuple[dict, object]:
        rules = await AutoRuleRepository.list_rules_by_user(session, user.id)
        payload = AutoRuleListPayload(rules=[_serialize_rule(rule) for rule in rules])
        return payload.model_dump(mode="json"), RESPONSE.ok("auto rules ready")

    @staticmethod
    async def create_rule(
        session: AsyncSession,
        user: User,
        request: AutoRuleCreateRequest,
    ) -> tuple[dict, object]:
        try:
            normalized_pair = _validate_pair(request.pair)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        rule = AutoDecisionRule(
            user_id=user.id,
            pair=normalized_pair,
            trigger_mode=request.trigger_mode,
            rate_condition=request.rate_condition,
            target_rate=request.target_rate,
            signal_condition=request.signal_condition,
            watch_amount=request.watch_amount,
            quiet_hours_start=request.quiet_hours_start,
            quiet_hours_end=request.quiet_hours_end,
            cooldown_minutes=request.cooldown_minutes,
            notes=request.notes,
            is_active=request.is_active,
        )
        rule = await AutoRuleRepository.create_rule(session, rule)
        await AutoRuleService._evaluate_rule(session, rule)
        await session.commit()
        return _serialize_rule(rule).model_dump(mode="json"), RESPONSE.ok("auto rule created")

    @staticmethod
    async def update_rule(
        session: AsyncSession,
        user: User,
        rule_id: str,
        request: AutoRuleUpdateRequest,
    ) -> tuple[dict, object]:
        rule = await AutoRuleRepository.get_rule(session, rule_id)
        if not rule or rule.user_id != user.id:
            return {}, RESPONSE.error(404, "auto rule not found")

        try:
            merged = _merged_rule_payload(rule, request)
            normalized_pair = _validate_pair(merged.pair)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        rule.pair = normalized_pair
        rule.trigger_mode = merged.trigger_mode
        rule.rate_condition = merged.rate_condition
        rule.target_rate = merged.target_rate
        rule.signal_condition = merged.signal_condition
        rule.watch_amount = merged.watch_amount
        rule.quiet_hours_start = merged.quiet_hours_start
        rule.quiet_hours_end = merged.quiet_hours_end
        rule.cooldown_minutes = merged.cooldown_minutes
        rule.notes = merged.notes
        rule.is_active = merged.is_active

        await AutoRuleService._evaluate_rule(session, rule)
        await session.commit()
        await session.refresh(rule)
        return _serialize_rule(rule).model_dump(mode="json"), RESPONSE.ok("auto rule updated")

    @staticmethod
    async def delete_rule(session: AsyncSession, user: User, rule_id: str) -> tuple[dict, object]:
        rule = await AutoRuleRepository.get_rule(session, rule_id)
        if not rule or rule.user_id != user.id:
            return {}, RESPONSE.error(404, "auto rule not found")

        rule.is_active = False
        await session.commit()
        await session.refresh(rule)
        return _serialize_rule(rule).model_dump(mode="json"), RESPONSE.ok("auto rule deleted")

    @staticmethod
    async def get_history(
        session: AsyncSession,
        user: User,
        rule_id: str | None,
        limit: int,
    ) -> tuple[dict, object]:
        if rule_id:
            rule = await AutoRuleRepository.get_rule(session, rule_id)
            if not rule or rule.user_id != user.id:
                return {}, RESPONSE.error(404, "auto rule not found")

        items = await AutoRuleRepository.list_history_by_user(session, user.id, rule_id=rule_id, limit=limit)
        payload = AlertHistoryListPayload(items=[_serialize_history(item) for item in items])
        return payload.model_dump(mode="json"), RESPONSE.ok("auto rule history ready")

    @staticmethod
    async def _evaluate_rule(session: AsyncSession, rule: AutoDecisionRule) -> None:
        if not rule.is_active:
            return

        current_time = _now_local()
        if _is_in_quiet_hours(rule, current_time):
            return

        if rule.last_triggered_at is not None:
            last_triggered = rule.last_triggered_at.astimezone(LOCAL_TZ)
            if current_time < last_triggered + timedelta(minutes=rule.cooldown_minutes):
                return

        if rule.trigger_mode == "rate":
            live_payload, response = await RateService.get_live_rates()
            if response.status_code >= 300:
                return
            current_rate = next(
                (item["rate"] for item in live_payload["pairs"] if item["pair"] == rule.pair),
                None,
            )
            if current_rate is None or not _is_rate_triggered(rule, float(current_rate)):
                return
            message = (
                f"{rule.pair} current rate {current_rate} met {rule.rate_condition} {rule.target_rate}. "
                f"Notification only; no automatic exchange was executed. {DISCLAIMER}"
            )
            history = AlertHistory(
                rule_id=rule.id,
                user_id=rule.user_id,
                pair=rule.pair,
                trigger_mode=rule.trigger_mode,
                evaluated_value=f"{float(current_rate):.4f}",
                signal_value=None,
                message=message,
            )
        else:
            report_payload, response = await DailyReportService.get_today_report(session)
            if response.status_code >= 300:
                return
            signal_value = report_payload[PAIR_SIGNAL_FIELD[rule.pair]]
            if signal_value != rule.signal_condition:
                return
            message = (
                f"{rule.pair} daily AI signal is {signal_value}. Notification only; "
                f"no automatic exchange was executed. {DISCLAIMER}"
            )
            history = AlertHistory(
                rule_id=rule.id,
                user_id=rule.user_id,
                pair=rule.pair,
                trigger_mode=rule.trigger_mode,
                evaluated_value=None,
                signal_value=signal_value,
                message=message,
            )

        await AutoRuleRepository.create_history(session, history)
        rule.last_triggered_at = current_time.astimezone()
