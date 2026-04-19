from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class AutoDecisionRule(Base):
    __tablename__ = "auto_decision_rules"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: uuid4().hex)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    pair: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    trigger_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    rate_condition: Mapped[str | None] = mapped_column(String(16), nullable=True)
    target_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal_condition: Mapped[str | None] = mapped_column(String(16), nullable=True)
    watch_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    quiet_hours_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quiet_hours_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
