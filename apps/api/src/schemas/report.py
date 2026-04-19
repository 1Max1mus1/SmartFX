from datetime import date, datetime

from pydantic import BaseModel


class DailyReportPayload(BaseModel):
    report_date: date
    generated_at: datetime
    summary_markdown: str
    signal_usd_cny: str
    signal_hkd_cny: str
    signal_usd_hkd: str
    rates_snapshot: dict

