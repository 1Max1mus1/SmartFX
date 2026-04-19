from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.exchange_record import ExchangeRecord


class RecordRepository:
    @staticmethod
    async def create(session: AsyncSession, record: ExchangeRecord) -> ExchangeRecord:
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return record

    @staticmethod
    async def list_by_user(session: AsyncSession, user_id: str) -> list[ExchangeRecord]:
        result = await session.execute(
            select(ExchangeRecord)
            .where(ExchangeRecord.user_id == user_id)
            .order_by(ExchangeRecord.exchange_date.desc(), ExchangeRecord.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_recent_by_user(session: AsyncSession, user_id: str, limit: int = 10) -> list[ExchangeRecord]:
        records = await RecordRepository.list_by_user(session, user_id)
        return records[:limit]

    @staticmethod
    async def get_by_id(session: AsyncSession, record_id: str) -> ExchangeRecord | None:
        result = await session.execute(select(ExchangeRecord).where(ExchangeRecord.id == record_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(session: AsyncSession, record: ExchangeRecord) -> None:
        await session.delete(record)
