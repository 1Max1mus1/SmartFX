from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    rule_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("auto_decision_rules.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    pair: Mapped[str] = mapped_column(String(7), nullable=False)
    trigger_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    evaluated_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signal_value: Mapped[str | None] = mapped_column(String(16), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_channel: Mapped[str] = mapped_column(String(32), nullable=False, default="email")
    delivery_status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
