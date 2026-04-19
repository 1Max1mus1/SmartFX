from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.report_job import ReportJob


class ReportJobRepository:
    @staticmethod
    async def create(session: AsyncSession, job: ReportJob) -> ReportJob:
        session.add(job)
        await session.flush()
        await session.refresh(job)
        return job

    @staticmethod
    async def get_by_id(session: AsyncSession, job_id: str) -> ReportJob | None:
        result = await session.execute(select(ReportJob).where(ReportJob.id == job_id))
        return result.scalar_one_or_none()

