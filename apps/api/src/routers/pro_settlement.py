from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.format import router_response_handler
from src.schemas.settlement import SettlementRequest
from src.services.auth_service import get_current_pro_user
from src.services.db import get_db_session
from src.services.settlement_service import SettlementService

router = APIRouter()


@router.post("/settlement")
async def analyze_settlement(
    request: SettlementRequest,
    _: User = Depends(get_current_pro_user),
):
    payload, response = await SettlementService.analyze(request)
    router_response_handler(response)
    return payload

