from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.exchange_record import ExchangeRecord
from src.models.user import User
from src.repositories.record_repository import RecordRepository
from src.schemas.format import ResponseFormatter
from src.schemas.records import ExchangeRecordCreate, ExchangeRecordPayload, ExchangeRecordUpdate
from src.services.rate_service import get_conversion_rate

RESPONSE = ResponseFormatter(prefix="[RecordService]")

ALLOWED_CURRENCIES = {"USD", "HKD", "CNY"}


def _normalize_currency(code: str) -> str:
    normalized = code.upper()
    if normalized not in ALLOWED_CURRENCIES:
        raise ValueError(f"unsupported currency: {code}")
    return normalized


def _serialize_record(record: ExchangeRecord) -> ExchangeRecordPayload:
    current_rate = get_conversion_rate(record.from_currency, record.to_currency)
    reference_pnl = round((record.from_amount * current_rate) - record.to_amount, 4)
    return ExchangeRecordPayload(
        id=record.id,
        user_id=record.user_id,
        from_currency=record.from_currency,
        to_currency=record.to_currency,
        from_amount=record.from_amount,
        to_amount=record.to_amount,
        rate_used=record.rate_used,
        exchange_date=record.exchange_date,
        purpose=record.purpose,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at,
        reference_pnl=reference_pnl,
    )


class RecordService:
    @staticmethod
    async def list_records(session: AsyncSession, user: User) -> tuple[dict, object]:
        records = await RecordRepository.list_by_user(session, user.id)
        payload = {"items": [_serialize_record(record).model_dump(mode="json") for record in records]}
        return payload, RESPONSE.ok("records ready")

    @staticmethod
    async def create_record(
        session: AsyncSession,
        user: User,
        request: ExchangeRecordCreate,
    ) -> tuple[dict, object]:
        try:
            from_currency = _normalize_currency(request.from_currency)
            to_currency = _normalize_currency(request.to_currency)
            get_conversion_rate(from_currency, to_currency)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        record = ExchangeRecord(
            user_id=user.id,
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=request.from_amount,
            to_amount=request.to_amount,
            rate_used=request.rate_used,
            exchange_date=request.exchange_date,
            purpose=request.purpose,
            notes=request.notes,
        )
        record = await RecordRepository.create(session, record)
        await session.commit()
        return _serialize_record(record).model_dump(mode="json"), RESPONSE.ok("record created")

    @staticmethod
    async def update_record(
        session: AsyncSession,
        user: User,
        record_id: str,
        request: ExchangeRecordUpdate,
    ) -> tuple[dict, object]:
        record = await RecordRepository.get_by_id(session, record_id)
        if not record or record.user_id != user.id:
            return {}, RESPONSE.error(404, "record not found")

        for field_name, value in request.model_dump(exclude_unset=True).items():
            setattr(record, field_name, value)

        await session.commit()
        await session.refresh(record)
        return _serialize_record(record).model_dump(mode="json"), RESPONSE.ok("record updated")

    @staticmethod
    async def delete_record(session: AsyncSession, user: User, record_id: str) -> tuple[dict, object]:
        record = await RecordRepository.get_by_id(session, record_id)
        if not record or record.user_id != user.id:
            return {}, RESPONSE.error(404, "record not found")

        await RecordRepository.delete(session, record)
        await session.commit()
        return {"deleted": True, "id": record_id}, RESPONSE.ok("record deleted")


def require_current_user(user: User) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="authentication required")
    return user
