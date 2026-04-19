from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class AutoRuleBase(BaseModel):
    pair: str = Field(..., min_length=7, max_length=7)
    trigger_mode: str = Field(..., pattern="^(rate|ai_signal)$")
    rate_condition: str | None = Field(default=None, pattern="^(above|below)$")
    target_rate: float | None = Field(default=None, gt=0)
    signal_condition: str | None = Field(default=None, pattern="^(buy|hold|sell)$")
    watch_amount: float | None = Field(default=None, gt=0)
    quiet_hours_start: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=None, ge=0, le=23)
    cooldown_minutes: int = Field(default=120, ge=0, le=1440)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_by_mode(self):
        if self.trigger_mode == "rate":
            if not self.rate_condition or self.target_rate is None:
                raise ValueError("rate rules require rate_condition and target_rate")
            if self.signal_condition is not None:
                raise ValueError("rate rules do not accept signal_condition")
        if self.trigger_mode == "ai_signal":
            if not self.signal_condition:
                raise ValueError("ai_signal rules require signal_condition")
            if self.rate_condition is not None or self.target_rate is not None:
                raise ValueError("ai_signal rules do not accept rate_condition or target_rate")
        if (self.quiet_hours_start is None) ^ (self.quiet_hours_end is None):
            raise ValueError("quiet hours require both start and end")
        return self


class AutoRuleCreateRequest(AutoRuleBase):
    pass


class AutoRuleUpdateRequest(BaseModel):
    pair: str | None = Field(default=None, min_length=7, max_length=7)
    trigger_mode: str | None = Field(default=None, pattern="^(rate|ai_signal)$")
    rate_condition: str | None = Field(default=None, pattern="^(above|below)$")
    target_rate: float | None = Field(default=None, gt=0)
    signal_condition: str | None = Field(default=None, pattern="^(buy|hold|sell)$")
    watch_amount: float | None = Field(default=None, gt=0)
    quiet_hours_start: int | None = Field(default=None, ge=0, le=23)
    quiet_hours_end: int | None = Field(default=None, ge=0, le=23)
    cooldown_minutes: int | None = Field(default=None, ge=0, le=1440)
    notes: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class AutoRulePayload(AutoRuleBase):
    id: str
    last_triggered_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AutoRuleListPayload(BaseModel):
    rules: list[AutoRulePayload]


class AlertHistoryPayload(BaseModel):
    id: str
    rule_id: str
    pair: str
    trigger_mode: str
    evaluated_value: str | None
    signal_value: str | None
    message: str
    notification_channel: str
    delivery_status: str
    created_at: datetime


class AlertHistoryListPayload(BaseModel):
    items: list[AlertHistoryPayload]
