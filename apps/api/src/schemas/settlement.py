from datetime import date, datetime

from pydantic import BaseModel, Field


class SettlementRequest(BaseModel):
    amount: float = Field(..., gt=0)
    source_currency: str = Field(..., min_length=3, max_length=3)
    target_currency: str = Field(..., min_length=3, max_length=3)
    arrival_date: date
    optimization_goal: str = Field(..., pattern="^(maximize_income|minimize_cost)$")
    target_rate: float | None = Field(default=None, gt=0)
    latest_settlement_date: date | None = None


class SettlementAnalysisPayload(BaseModel):
    pair: str
    current_rate: float
    current_percentile_30d: float
    current_percentile_90d: float
    immediate_value: float
    projected_best_case_value: float
    estimated_delta: float
    recommended_window_days: int
    recommended_window_end_date: date
    recommended_window_reason: str
    zone_label: str
    narrative: str
    disclaimer: str


class SettlementReportRequest(BaseModel):
    settlement_data: SettlementRequest


class ReportJobCreatePayload(BaseModel):
    job_id: str
    job_status: str
    created_at: datetime


class ReportJobStatusPayload(BaseModel):
    job_id: str
    job_status: str
    result: dict | None
    error_message: str | None
    updated_at: datetime
