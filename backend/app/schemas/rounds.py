import uuid
from datetime import date, datetime

from pydantic import BaseModel


class RoundCounts(BaseModel):
    total: int
    SUBIR: int
    BAIXAR: int
    MANTER: int
    REVISAR: int


class RoundOut(BaseModel):
    id: uuid.UUID
    round_date: date
    source: str
    created_at: datetime
    counts: RoundCounts


class TopValueAtStake(BaseModel):
    recommendation_id: uuid.UUID
    sku: str
    product: str
    channel: str
    value: float


class RoundSummary(BaseModel):
    round_id: uuid.UUID
    round_date: date
    total: int
    with_change: int
    by_recommendation: dict[str, int]
    review_reasons: dict[str, int]
    requires_approval: int
    top_value_at_stake: TopValueAtStake | None
    decided: int
    pending: int
    summary_text: str


class ImportResult(BaseModel):
    round_id: uuid.UUID
    round_date: date
    imported: int
