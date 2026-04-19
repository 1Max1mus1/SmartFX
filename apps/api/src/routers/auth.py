from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.auth import LoginRequest, RegisterRequest
from src.schemas.format import router_response_handler
from src.services.auth_service import AuthService
from src.services.db import get_db_session

router = APIRouter()


@router.post("/register")
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    payload, response = await AuthService.register(session, request.email, request.password, request.plan)
    router_response_handler(response)
    return payload


@router.post("/login")
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
):
    payload, response = await AuthService.login(session, request.email, request.password)
    router_response_handler(response)
    return payload
