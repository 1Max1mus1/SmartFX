from datetime import date, datetime

from pydantic import BaseModel, Field


class RateQuote(BaseModel):
    pair: str
    rate: float = Field(..., gt=0)
    change_pct_24h: float
    updated_at: datetime
    source: str


class RateHistoryPoint(BaseModel):
    day: date
    rate: float = Field(..., gt=0)


class LiveRatesPayload(BaseModel):
    updated_at: datetime
    pairs: list[RateQuote]


class RateHistoryPayload(BaseModel):
    pair: str
    days: int
    points: list[RateHistoryPoint]


class RateStatsPayload(BaseModel):
    pair: str
    days: int
    current: float
    high: float
    low: float
    average: float
    percentile: float
    change_pct_24h: float

