import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models import DecisionType


class DecisionOut(BaseModel):
    id: uuid.UUID
    recommendation_id: uuid.UUID
    round_date: str | None = None
    user_id: uuid.UUID
    user_name: str
    decision: str
    applied_price: float | None
    rejection_reason: str | None
    comment: str | None
    snapshot_recommendation: str
    snapshot_suggested_price: float
    snapshot_current_price: float
    created_at: datetime


class DecisionIn(BaseModel):
    user_id: uuid.UUID
    decision: DecisionType
    applied_price: float | None = None
    rejection_reason: str | None = None
    comment: str | None = None


class DecisionCreated(BaseModel):
    decision: DecisionOut
    warnings: list[str]


class HistoryItem(DecisionOut):
    sku: str
    product_name: str
    channel: str
