from datetime import date, datetime

from pydantic import BaseModel, Field


class BacktestOverviewSignal(BaseModel):
    signal: str
    total_signals: int
    match_rate_7d: float
    match_rate_14d: float


class BacktestOverviewPayload(BaseModel):
    pair: str
    days: int
    baseline: float
    composite_reference_index: float
    best_signal_type: str
    note: str
    signals: list[BacktestOverviewSignal]


class PersonalBacktestRequest(BaseModel):
    period_start: date
    period_end: date
    pair: str = Field(..., min_length=7, max_length=7)


class PersonalBacktestResultPayload(BaseModel):
    pair: str
    period_start: date
    period_end: date
    record_count: int
    base_amount: float
    actual_avg_rate: float
    simulated_avg_rate: float
    diff_amount: float
    summary: str
    disclaimer: str


class BacktestJobCreatePayload(BaseModel):
    job_id: str
    job_status: str
    created_at: datetime


class BacktestJobStatusPayload(BaseModel):
    job_id: str
    job_status: str
    result: dict | None
    error_message: str | None
    updated_at: datetime
