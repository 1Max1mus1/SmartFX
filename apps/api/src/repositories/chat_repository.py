from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.chat_message import ChatMessage
from src.models.chat_session import ChatSession


class ChatRepository:
    @staticmethod
    async def get_session(session: AsyncSession, session_id: str) -> ChatSession | None:
        result = await session.execute(select(ChatSession).where(ChatSession.id == session_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_session(session: AsyncSession, chat_session: ChatSession) -> ChatSession:
        session.add(chat_session)
        await session.flush()
        await session.refresh(chat_session)
        return chat_session

    @staticmethod
    async def add_message(session: AsyncSession, message: ChatMessage) -> ChatMessage:
        session.add(message)
        await session.flush()
        await session.refresh(message)
        return message

    @staticmethod
    async def list_messages(session: AsyncSession, session_id: str, limit: int = 20) -> list[ChatMessage]:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = list(result.scalars().all())
        return messages[-limit:]

