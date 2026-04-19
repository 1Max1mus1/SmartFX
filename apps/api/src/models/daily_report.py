from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class DailyReport(Base):
    __tablename__ = "daily_reports"

    signal_usd_cny_enum = Enum("buy", "hold", "sell", name="signal_enum")
    signal_hkd_cny_enum = Enum("buy", "hold", "sell", name="signal_enum2")
    signal_usd_hkd_enum = Enum("buy", "hold", "sell", name="signal_enum3")
    signal_hkd_usd_enum = Enum("buy", "hold", "sell", name="signal_enum4")

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: uuid4().hex)
    report_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    rates_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    ai_content: Mapped[str] = mapped_column(Text, nullable=False)
    signal_usd_cny: Mapped[str | None] = mapped_column(signal_usd_cny_enum, nullable=True)
    signal_hkd_cny: Mapped[str | None] = mapped_column(signal_hkd_cny_enum, nullable=True)
    signal_usd_hkd: Mapped[str | None] = mapped_column(signal_usd_hkd_enum, nullable=True)
    signal_hkd_usd: Mapped[str | None] = mapped_column(signal_hkd_usd_enum, nullable=True)
    rates_7d_after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rates_14d_after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
