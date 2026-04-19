from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.format import router_response_handler
from src.services.auth_service import get_current_user
from src.services.daily_report_service import DailyReportService
from src.services.db import get_db_session

router = APIRouter()


@router.get("/daily")
async def get_daily_report(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
):
    payload, response = await DailyReportService.get_today_report(session)
    router_response_handler(response)
    return payload

