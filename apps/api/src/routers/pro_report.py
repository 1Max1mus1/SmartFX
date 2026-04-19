from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.format import router_response_handler
from src.schemas.settlement import SettlementReportRequest
from src.services.auth_service import get_current_pro_user
from src.services.db import get_db_session
from src.services.pro_report_service import ProReportService

router = APIRouter()


@router.post("/report/generate")
async def generate_settlement_report(
    request: SettlementReportRequest,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await ProReportService.create_report_job(session, user, request.settlement_data)
    router_response_handler(response)
    return payload


@router.get("/report/status/{job_id}")
async def get_report_status(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await ProReportService.get_report_job_status(session, user, job_id)
    router_response_handler(response)
    return payload

