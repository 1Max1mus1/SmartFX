from __future__ import annotations

from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.kimi_client import KimiClient
from src.models.daily_report import DailyReport
from src.repositories.report_repository import ReportRepository
from src.schemas.format import ResponseFormatter
from src.schemas.report import DailyReportPayload
from src.services.rate_service import RateService

RESPONSE = ResponseFormatter(prefix="[DailyReportService]")


def _classify_signal(percentile: float) -> dict[str, str]:
    if percentile <= 35:
        return {"label": "低位", "signal": "buy"}
    if percentile >= 65:
        return {"label": "高位", "signal": "sell"}
    return {"label": "中位", "signal": "hold"}


def _trend_summary(stats_map: dict) -> str:
    usd_change = stats_map["USD/CNY"]["change_pct_24h"]
    if usd_change >= 0.2:
        return "美元兑人民币短期偏强，如果不是刚需换汇，可以继续观察并分批执行。"
    if usd_change <= -0.2:
        return "美元兑人民币短期偏弱，如果这周有刚需换汇，可以关注回落后的执行窗口。"
    return "主要货币对短期仍以震荡为主，更适合结合刚需场景分批安排。"


class DailyReportService:
    @staticmethod
    async def get_today_report(session: AsyncSession) -> tuple[dict, object]:
        today = date.today()
        report = await ReportRepository.get_by_date(session, today)
        if not report:
            payload, response = await DailyReportService.generate_today_report(session)
            return payload, response
        return DailyReportService._serialize(report), RESPONSE.ok("daily report ready")

    @staticmethod
    async def generate_today_report(session: AsyncSession) -> tuple[dict, object]:
        existing = await ReportRepository.get_by_date(session, date.today())
        if existing:
            return DailyReportService._serialize(existing), RESPONSE.ok("daily report already exists")

        live_payload, live_response = await RateService.get_live_rates()
        if live_response.status_code >= 300:
            return {}, live_response

        stats_map = {}
        signals = {}
        for pair in ("USD/CNY", "HKD/CNY", "USD/HKD"):
            stats_payload, stats_response = await RateService.get_stats(pair, 90)
            if stats_response.status_code >= 300:
                return {}, stats_response
            stats_map[pair] = stats_payload
            signals[pair] = _classify_signal(stats_payload["percentile"])

        context = {
            "live_map": {item["pair"]: item for item in live_payload["pairs"]},
            "stats_map": stats_map,
            "signals": signals,
            "trend_summary": _trend_summary(stats_map),
            "news_headlines": [
                "美元指数仍在关键区间内反复震荡，市场继续等待新的利率路径指引。",
                "人民币中间价延续稳中微调，短期政策预期保持平稳。",
                "港元联系汇率区间整体稳定，套息交易热度有所降温。",
            ],
            "reference_signal": "如果是刚需换汇，优先考虑分批执行；如果是结算场景，可以重点关注高位兑现窗口。",
        }
        ai_payload = await KimiClient().generate_daily_report(context)

        report = DailyReport(
            report_date=date.today(),
            rates_snapshot=live_payload,
            ai_content=ai_payload["summary_markdown"],
            signal_usd_cny=ai_payload["signals"]["signal_usd_cny"],
            signal_hkd_cny=ai_payload["signals"]["signal_hkd_cny"],
            signal_usd_hkd=ai_payload["signals"]["signal_usd_hkd"],
            signal_hkd_usd="hold",
            rates_7d_after=None,
            rates_14d_after=None,
            is_simulated=False,
        )
        try:
            report = await ReportRepository.create(session, report)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            existing = await ReportRepository.get_by_date(session, date.today())
            if existing:
                return DailyReportService._serialize(existing), RESPONSE.ok("daily report already exists")
            raise

        return DailyReportService._serialize(report), RESPONSE.ok("daily report generated")

    @staticmethod
    def _serialize(report: DailyReport) -> dict:
        payload = DailyReportPayload(
            report_date=report.report_date,
            generated_at=report.created_at,
            summary_markdown=report.ai_content,
            signal_usd_cny=report.signal_usd_cny,
            signal_hkd_cny=report.signal_hkd_cny,
            signal_usd_hkd=report.signal_usd_hkd,
            rates_snapshot=report.rates_snapshot,
        )
        return payload.model_dump(mode="json")
