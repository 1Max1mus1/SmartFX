from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.auto_rules import AutoRuleCreateRequest, AutoRuleUpdateRequest
from src.schemas.format import router_response_handler
from src.services.auth_service import get_current_pro_user
from src.services.auto_rule_service import AutoRuleService
from src.services.db import get_db_session

router = APIRouter()


@router.get("/auto-rules")
async def list_auto_rules(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await AutoRuleService.list_rules(session, user)
    router_response_handler(response)
    return payload


@router.post("/auto-rules")
async def create_auto_rule(
    request: AutoRuleCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await AutoRuleService.create_rule(session, user, request)
    router_response_handler(response)
    return payload


@router.patch("/auto-rules/{rule_id}")
async def update_auto_rule(
    rule_id: str,
    request: AutoRuleUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await AutoRuleService.update_rule(session, user, rule_id, request)
    router_response_handler(response)
    return payload


@router.delete("/auto-rules/{rule_id}")
async def delete_auto_rule(
    rule_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await AutoRuleService.delete_rule(session, user, rule_id)
    router_response_handler(response)
    return payload


@router.get("/auto-rules/history")
async def get_auto_rule_history(
    rule_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_pro_user),
):
    payload, response = await AutoRuleService.get_history(session, user, rule_id, limit)
    router_response_handler(response)
    return payload
