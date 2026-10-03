import uuid
from datetime import date, datetime

from pydantic import BaseModel


class DayCount(BaseModel):
    date: date
    count: int


class AnalystSummary(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    decisions_total: int
    by_decision: dict[str, int]
    acceptance_rate: float | None
    acceptance_base: int
    rounds_count: int
    decisions_last_7_days: int
    last_activity_at: datetime | None


class AnalystDetail(AnalystSummary):
    decisions_by_day: list[DayCount]
    by_recommendation: dict[str, int]
    rejection_reasons: dict[str, int]
