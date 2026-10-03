import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models import SyncFrequency


class SyncRunOut(BaseModel):
    id: uuid.UUID
    trigger: str
    source: str
    status: str
    user_name: str | None
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    reference_date: date | None
    products_total: int
    products_new: int
    products_updated: int
    prices_changed: int
    history_imported: int
    stock_updated: int
    message: str | None


class ScheduleOut(BaseModel):
    enabled: bool
    frequency: SyncFrequency
    weekday: int | None
    day_of_month: int | None
    time_of_day: str  # HH:MM
    description: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    updated_by_name: str | None
    updated_at: datetime | None


class ScheduleIn(BaseModel):
    enabled: bool
    frequency: SyncFrequency
    weekday: int | None = Field(None, description="0 = segunda … 6 = domingo (semanal)")
    day_of_month: int | None = Field(None, description="1 a 28 (mensal)")
    time_of_day: str = Field("06:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    user_id: uuid.UUID | None = None


class SchedulePreview(BaseModel):
    description: str
    next_run_at: datetime


class SyncRequest(BaseModel):
    user_id: uuid.UUID | None = None


class ErpStatus(BaseModel):
    source: str
    source_file: str
    last_sync: SyncRunOut | None
    last_success: SyncRunOut | None
    schedule: ScheduleOut
    products: int
    channel_prices: int
    price_changes: int
    last_reference_date: date | None
