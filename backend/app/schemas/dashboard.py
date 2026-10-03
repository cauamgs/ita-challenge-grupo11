import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.analysts import DayCount
from app.schemas.erp import ScheduleOut, SyncRunOut
from app.schemas.metrics import MetricValue, TopItem


class RoundProgress(BaseModel):
    round_id: uuid.UUID
    round_date: date
    total: int
    with_change: int
    by_recommendation: dict[str, int]
    decided: int
    pending: int
    postponed: int
    no_action: int
    requires_approval_pending: int
    high_risk_pending: int
    summary_text: str


class RoundKpis(BaseModel):
    acceptance_rate: MetricValue
    estimated_review_hours: MetricValue
    in_competitive_band: MetricValue
    avg_gross_margin: MetricValue


class MonthChanges(BaseModel):
    month: str  # AAAA-MM
    increases: int
    decreases: int


class ActivityItem(BaseModel):
    kind: str  # DECISAO | SYNC
    at: datetime
    title: str
    detail: str | None
    user_name: str | None
    link: str | None


class AnalystActivity(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    decisions_total: int
    decisions_round: int


class ErpSummary(BaseModel):
    last_sync: SyncRunOut | None
    schedule: ScheduleOut
    products: int
    last_reference_date: date | None


class Dashboard(BaseModel):
    round: RoundProgress | None
    kpis: RoundKpis | None
    top_pending: list[TopItem]
    erp: ErpSummary
    price_changes_by_month: list[MonthChanges]
    price_changes_90d: dict[str, int]
    decisions_by_day: list[DayCount]
    analysts: list[AnalystActivity]
    recent_activity: list[ActivityItem]
