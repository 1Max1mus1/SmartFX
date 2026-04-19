from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.backtest_cache import BacktestCache
from src.models.backtest_job import BacktestJob


class BacktestRepository:
    @staticmethod
    async def create_job(session: AsyncSession, job: BacktestJob) -> BacktestJob:
        session.add(job)
        await session.flush()
        await session.refresh(job)
        return job

    @staticmethod
    async def get_job(session: AsyncSession, job_id: str) -> BacktestJob | None:
        result = await session.execute(select(BacktestJob).where(BacktestJob.id == job_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_cache(session: AsyncSession, cache: BacktestCache) -> BacktestCache:
        session.add(cache)
        await session.flush()
        await session.refresh(cache)
        return cache

