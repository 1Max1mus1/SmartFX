from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.kimi_client import DISCLAIMER
from src.models.backtest_cache import BacktestCache
from src.models.backtest_job import BacktestJob
from src.models.user import User
from src.repositories.backtest_repository import BacktestRepository
from src.repositories.record_repository import RecordRepository
from src.schemas.backtest import (
    BacktestJobCreatePayload,
    BacktestJobStatusPayload,
    BacktestOverviewPayload,
    BacktestOverviewSignal,
    PersonalBacktestRequest,
    PersonalBacktestResultPayload,
)
from src.schemas.format import ResponseFormatter
from src.services.db import SessionLocal
from src.services.rate_service import get_rate_series

RESPONSE = ResponseFormatter(prefix="[BacktestService]")
SUPPORTED_BACKTEST_PAIRS = {"USD/CNY", "HKD/CNY", "USD/HKD"}


def _normalize_pair(pair: str) -> str:
    normalized = pair.upper()
    if normalized not in SUPPORTED_BACKTEST_PAIRS:
        raise ValueError(f"unsupported pair: {pair}")
    return normalized


def _signal_for_percentile(percentile: float) -> str:
    if percentile <= 35:
        return "buy"
    if percentile >= 65:
        return "sell"
    return "hold"


def _is_match(signal: str, current_rate: float, future_rate: float) -> bool:
    diff_ratio = (future_rate - current_rate) / current_rate
    if signal == "buy":
        return diff_ratio > 0
    if signal == "sell":
        return diff_ratio < 0
    return abs(diff_ratio) <= 0.01


def _round_rate(value: float) -> float:
    return round(value, 4)


class BacktestService:
    @staticmethod
    async def get_overview(pair: str, days: int) -> tuple[dict, object]:
        try:
            normalized_pair = _normalize_pair(pair)
            if days not in {30, 60, 90}:
                raise ValueError(f"unsupported days window: {days}")
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        full_series = get_rate_series(normalized_pair, days + 45)
        start_index = len(full_series) - days - 15
        signal_stats: dict[str, dict[str, float]] = {
            "buy": {"count": 0, "match7": 0, "match14": 0},
            "hold": {"count": 0, "match7": 0, "match14": 0},
            "sell": {"count": 0, "match7": 0, "match14": 0},
        }

        for index in range(max(30, start_index), len(full_series) - 14):
            trailing = [point.rate for point in full_series[index - 30 : index]]
            current_rate = full_series[index].rate
            percentile = round((sum(1 for value in trailing if value <= current_rate) / len(trailing)) * 100, 2)
            signal = _signal_for_percentile(percentile)
            signal_stats[signal]["count"] += 1
            if _is_match(signal, current_rate, full_series[index + 7].rate):
                signal_stats[signal]["match7"] += 1
            if _is_match(signal, current_rate, full_series[index + 14].rate):
                signal_stats[signal]["match14"] += 1

        signals_payload: list[BacktestOverviewSignal] = []
        composite_values: list[float] = []
        best_signal_type = "hold"
        best_score = -1.0

        for signal_name, stats in signal_stats.items():
            count = int(stats["count"])
            match_rate_7d = round((stats["match7"] / count) * 100, 2) if count else 0.0
            match_rate_14d = round((stats["match14"] / count) * 100, 2) if count else 0.0
            score = (match_rate_7d + match_rate_14d) / 2
            if count:
                composite_values.append(score)
            if score > best_score:
                best_score = score
                best_signal_type = signal_name
            signals_payload.append(
                BacktestOverviewSignal(
                    signal=signal_name,
                    total_signals=count,
                    match_rate_7d=match_rate_7d,
                    match_rate_14d=match_rate_14d,
                )
            )

        composite_reference_index = round(sum(composite_values) / len(composite_values), 2) if composite_values else 0.0
        payload = BacktestOverviewPayload(
            pair=normalized_pair,
            days=days,
            baseline=50.0,
            composite_reference_index=composite_reference_index,
            best_signal_type=best_signal_type,
            note="历史表现不代表未来，仅供参考。",
            signals=signals_payload,
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("backtest overview ready")

    @staticmethod
    async def create_personal_backtest_job(
        session: AsyncSession,
        user: User,
        request: PersonalBacktestRequest,
    ) -> tuple[dict, object]:
        try:
            normalized_pair = _normalize_pair(request.pair)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        job = BacktestJob(
            user_id=user.id,
            pair=normalized_pair,
            job_status="pending",
            input_payload=json.dumps(request.model_dump(mode="json"), ensure_ascii=False),
        )
        job = await BacktestRepository.create_job(session, job)
        await session.commit()

        asyncio.get_running_loop().create_task(BacktestService._run_personal_backtest(job.id))
        payload = BacktestJobCreatePayload(job_id=job.id, job_status=job.job_status, created_at=job.created_at)
        return payload.model_dump(mode="json"), RESPONSE.ok("personal backtest job created")

    @staticmethod
    async def get_personal_backtest_result(
        session: AsyncSession,
        user: User,
        job_id: str,
    ) -> tuple[dict, object]:
        job = await BacktestRepository.get_job(session, job_id)
        if not job or job.user_id != user.id:
            return {}, RESPONSE.error(404, "backtest job not found")

        payload = BacktestJobStatusPayload(
            job_id=job.id,
            job_status=job.job_status,
            result=json.loads(job.result_payload) if job.result_payload else None,
            error_message=job.error_message,
            updated_at=job.updated_at,
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("backtest job status ready")

    @staticmethod
    async def _run_personal_backtest(job_id: str) -> None:
        async with SessionLocal() as session:
            job = await BacktestRepository.get_job(session, job_id)
            if not job:
                return

            try:
                job.job_status = "running"
                await session.commit()

                request = PersonalBacktestRequest.model_validate(json.loads(job.input_payload))
                result_payload = await BacktestService._compute_personal_backtest(session, job.user_id, request)

                cache = BacktestCache(
                    user_id=job.user_id,
                    period_start=request.period_start,
                    period_end=request.period_end,
                    pair=request.pair,
                    actual_avg_rate=result_payload["actual_avg_rate"],
                    simulated_avg_rate=result_payload["simulated_avg_rate"],
                    diff_amount=result_payload["diff_amount"],
                    base_amount=result_payload["base_amount"],
                    base_currency=request.pair.split("/")[0],
                    result_payload=json.dumps(result_payload, ensure_ascii=False),
                )
                await BacktestRepository.create_cache(session, cache)

                job.result_payload = json.dumps(result_payload, ensure_ascii=False)
                job.job_status = "done"
                job.error_message = None
                await session.commit()
            except Exception as exc:
                job.job_status = "failed"
                job.error_message = str(exc)
                await session.commit()

    @staticmethod
    async def _compute_personal_backtest(
        session: AsyncSession,
        user_id: str,
        request: PersonalBacktestRequest,
    ) -> dict:
        records = await RecordRepository.list_by_user(session, user_id)
        pair_records = [
            record
            for record in records
            if f"{record.from_currency}/{record.to_currency}" == request.pair
            and request.period_start <= record.exchange_date <= request.period_end
        ]
        if not pair_records:
            raise RuntimeError("no exchange records found for selected period and pair")

        rate_lookup = {point.day.isoformat(): point.rate for point in get_rate_series(request.pair, 365)}
        sorted_days = sorted(rate_lookup.keys())

        actual_total = sum(record.rate_used * record.from_amount for record in pair_records)
        simulated_total = 0.0
        base_amount = round(sum(record.from_amount for record in pair_records), 4)

        for record in pair_records:
            start_day = record.exchange_date.isoformat()
            candidate_days = [day for day in sorted_days if start_day <= day <= request.period_end.isoformat()]
            candidate_days = candidate_days[:14] if len(candidate_days) > 14 else candidate_days
            if not candidate_days:
                candidate_days = [start_day]
            best_day = max(candidate_days, key=lambda day: rate_lookup.get(day, record.rate_used))
            simulated_total += rate_lookup.get(best_day, record.rate_used) * record.from_amount

        actual_avg_rate = _round_rate(actual_total / base_amount)
        simulated_avg_rate = _round_rate(simulated_total / base_amount)
        diff_amount = round(simulated_total - actual_total, 2)
        payload = PersonalBacktestResultPayload(
            pair=request.pair,
            period_start=request.period_start,
            period_end=request.period_end,
            record_count=len(pair_records),
            base_amount=base_amount,
            actual_avg_rate=actual_avg_rate,
            simulated_avg_rate=simulated_avg_rate,
            diff_amount=diff_amount,
            summary=(
                f"历史模拟显示，若在未来 14 天窗口中等待更优信号位执行，"
                f"平均参考汇率可由 {actual_avg_rate} 改善为 {simulated_avg_rate}，"
                f"参考差异约 {diff_amount}。"
            ),
            disclaimer=DISCLAIMER,
        )
        return payload.model_dump(mode="json")
