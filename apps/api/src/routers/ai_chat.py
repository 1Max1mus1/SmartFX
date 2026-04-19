from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.chat import ChatRequest
from src.schemas.format import router_response_handler
from src.services.auth_service import get_current_user
from src.services.chat_service import ChatService
from src.services.db import get_db_session

router = APIRouter()


@router.post("/chat")
async def ai_chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    payload, response = await ChatService.reply(
        session,
        user,
        message=request.message,
        session_id=request.session_id,
    )
    router_response_handler(response)
    return payload

