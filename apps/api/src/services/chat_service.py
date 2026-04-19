from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.kimi_client import KimiClient
from src.models.chat_message import ChatMessage
from src.models.chat_session import ChatSession
from src.models.user import User
from src.repositories.chat_repository import ChatRepository
from src.repositories.record_repository import RecordRepository
from src.schemas.chat import ChatResponsePayload, ChatMessagePayload
from src.schemas.format import ResponseFormatter
from src.services.daily_report_service import DailyReportService
from src.services.rate_service import RateService

RESPONSE = ResponseFormatter(prefix="[ChatService]")


def _title_from_message(message: str) -> str:
    trimmed = message.strip().replace("\n", " ")
    return trimmed[:32] if len(trimmed) > 32 else trimmed


class ChatService:
    @staticmethod
    async def reply(
        session: AsyncSession,
        user: User,
        *,
        message: str,
        session_id: str | None,
    ) -> tuple[dict, object]:
        if getattr(user, "id", None) == "demo-user":
            return await ChatService._reply_demo(session, message=message, session_id=session_id)

        chat_session = await ChatService._get_or_create_session(session, user, session_id, message)

        user_message = await ChatRepository.add_message(
            session,
            ChatMessage(session_id=chat_session.id, role="user", content=message),
        )

        daily_report_payload, daily_report_response = await DailyReportService.get_today_report(session)
        if daily_report_response.status_code >= 300:
            return {}, daily_report_response

        stats_map = {}
        for pair in ("USD/CNY", "HKD/CNY", "USD/HKD"):
            payload, _ = await RateService.get_stats(pair, 90)
            stats_map[pair] = payload

        records = await RecordRepository.list_recent_by_user(session, user.id, limit=10)
        reference_pnl_total = round(
            sum((record.from_amount * record.rate_used) - record.to_amount for record in records),
            4,
        )
        record_summary = {
            "count": len(records),
            "base_amount": round(sum(record.from_amount for record in records), 4),
            "reference_pnl_total": reference_pnl_total,
        }

        prior_messages = await ChatRepository.list_messages(session, chat_session.id, limit=20)
        prompt_history = [{"role": item.role, "content": item.content} for item in prior_messages[:-1]]
        answer = await KimiClient().chat(
            prompt=message,
            context={
                "daily_report_signal": daily_report_payload["signal_usd_cny"],
                "stats_map": stats_map,
                "record_summary": record_summary,
            },
            history=prompt_history,
        )

        assistant_message = await ChatRepository.add_message(
            session,
            ChatMessage(session_id=chat_session.id, role="assistant", content=answer),
        )
        await session.commit()

        messages = await ChatRepository.list_messages(session, chat_session.id, limit=20)
        payload = ChatResponsePayload(
            session_id=chat_session.id,
            answer=assistant_message.content,
            messages=[
                ChatMessagePayload(role=item.role, content=item.content, created_at=item.created_at)
                for item in messages
            ],
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("chat reply ready")

    @staticmethod
    async def _reply_demo(
        session: AsyncSession,
        *,
        message: str,
        session_id: str | None,
    ) -> tuple[dict, object]:
        daily_report_payload, daily_report_response = await DailyReportService.get_today_report(session)
        if daily_report_response.status_code >= 300:
            return {}, daily_report_response

        stats_map = {}
        for pair in ("USD/CNY", "HKD/CNY", "USD/HKD"):
            payload, _ = await RateService.get_stats(pair, 90)
            stats_map[pair] = payload

        answer = await KimiClient().chat(
            prompt=message,
            context={
                "daily_report_signal": daily_report_payload["signal_usd_cny"],
                "stats_map": stats_map,
                "record_summary": {
                    "count": 0,
                    "base_amount": 0,
                    "reference_pnl_total": 0,
                },
            },
            history=[],
        )

        now = datetime.now(UTC)
        payload = ChatResponsePayload(
            session_id=session_id or "demo-session",
            answer=answer,
            messages=[
                ChatMessagePayload(role="user", content=message, created_at=now),
                ChatMessagePayload(role="assistant", content=answer, created_at=now),
            ],
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("chat reply ready")

    @staticmethod
    async def _get_or_create_session(
        session: AsyncSession,
        user: User,
        session_id: str | None,
        message: str,
    ) -> ChatSession:
        if session_id:
            existing = await ChatRepository.get_session(session, session_id)
            if existing and existing.user_id == user.id:
                return existing

        chat_session = ChatSession(user_id=user.id, title=_title_from_message(message))
        return await ChatRepository.create_session(session, chat_session)
