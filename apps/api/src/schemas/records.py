from datetime import date, datetime

from pydantic import BaseModel, Field


class ExchangeRecordBase(BaseModel):
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    from_amount: float = Field(..., gt=0)
    to_amount: float = Field(..., gt=0)
    rate_used: float = Field(..., gt=0)
    exchange_date: date
    purpose: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)


class ExchangeRecordCreate(ExchangeRecordBase):
    pass


class ExchangeRecordUpdate(BaseModel):
    from_amount: float | None = Field(default=None, gt=0)
    to_amount: float | None = Field(default=None, gt=0)
    rate_used: float | None = Field(default=None, gt=0)
    exchange_date: date | None = None
    purpose: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)


class ExchangeRecordPayload(ExchangeRecordBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    reference_pnl: float

