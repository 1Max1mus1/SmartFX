from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.backtest import PersonalBacktestRequest
from src.schemas.format import router_response_handler
from src.services.auth_service import get_current_pro_user
from src.services.backtest_service import BacktestService
from src.services.db import get_db_session

router = APIRouter()


@router.get("/backtest/overview")
async def get_backtest_overview(
    pair: str = Query(..., description="Supported: USD/CNY, HKD/CNY, USD/HKD"),
    days: int = Query(90, description="Supported: 30, 60, 90"),
    _: User = Depends(get_current_pro_user),
):
    payload, response = await BacktestService.get_overview(pair, days)
    router_response_handler(response)
    return payload


@router.post("/backtest/personal")
async def create_personal_backtest(
    request: PersonalBacktestRequest,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await BacktestService.create_personal_backtest_job(session, user, request)
    router_response_handler(response)
    return payload


@router.get("/backtest/result/{job_id}")
async def get_personal_backtest_result(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await BacktestService.get_personal_backtest_result(session, user, job_id)
    router_response_handler(response)
    return payload

