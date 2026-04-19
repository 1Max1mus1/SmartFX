from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    session_id: str | None = None


class ChatMessagePayload(BaseModel):
    role: str
    content: str
    created_at: datetime


class ChatResponsePayload(BaseModel):
    session_id: str
    answer: str
    messages: list[ChatMessagePayload]
