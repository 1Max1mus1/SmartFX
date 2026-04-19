from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.daily_report import DailyReport


class ReportRepository:
    @staticmethod
    async def get_by_date(session: AsyncSession, report_date: date) -> DailyReport | None:
        result = await session.execute(select(DailyReport).where(DailyReport.report_date == report_date))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, report: DailyReport) -> DailyReport:
        session.add(report)
        await session.flush()
        await session.refresh(report)
        return report

