from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class StudentPaymentAdviceRequest(BaseModel):
    deadline_date: date
    amount: float | None = Field(default=None, gt=0)
    source_currency: str = Field(..., min_length=3, max_length=3)
    target_currency: str = Field(..., min_length=3, max_length=3)
    can_split_payment: bool
    risk_preference: Literal["stable", "balanced", "opportunistic"]
    notes: str | None = Field(default=None, max_length=500)


class StudentPaymentMarketSnapshotPayload(BaseModel):
    requested_pair: str
    reference_pair: str
    current_rate: float
    reference_rate: float
    change_pct_24h: float
    percentile_30d: float
    percentile_90d: float
    favorable_score_30d: float
    favorable_score_90d: float


class StudentPaymentAdvicePayload(BaseModel):
    decision: str
    decision_level: Literal["pay_now", "split_now", "watch_short"]
    decision_reason: str
    rate_assessment: str
    deadline_pressure: str
    suggested_action: str
    split_payment_plan: str | None = None
    market_snapshot: StudentPaymentMarketSnapshotPayload
    analysis_markdown: str
    disclaimer: str
