from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.format import router_response_handler
from src.schemas.records import ExchangeRecordCreate, ExchangeRecordUpdate
from src.services.auth_service import get_current_user
from src.services.db import get_db_session
from src.services.record_service import RecordService

router = APIRouter()


@router.get("")
async def list_records(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    payload, response = await RecordService.list_records(session, user)
    router_response_handler(response)
    return payload


@router.post("")
async def create_record(
    request: ExchangeRecordCreate,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    payload, response = await RecordService.create_record(session, user, request)
    router_response_handler(response)
    return payload


@router.patch("/{record_id}")
async def update_record(
    record_id: str,
    request: ExchangeRecordUpdate,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    payload, response = await RecordService.update_record(session, user, record_id, request)
    router_response_handler(response)
    return payload


@router.delete("/{record_id}")
async def delete_record(
    record_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    payload, response = await RecordService.delete_record(session, user, record_id)
    router_response_handler(response)
    return payload

