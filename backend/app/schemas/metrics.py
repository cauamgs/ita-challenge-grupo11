import uuid

from pydantic import BaseModel


class MetricValue(BaseModel):
    value: float | None
    target: float
    numerator: int | None = None
    denominator: int | None = None
    note: str | None = None


class TopItem(BaseModel):
    recommendation_id: uuid.UUID
    sku: str
    product_name: str
    channel: str
    recommendation: str
    variation: float
    value_at_stake: float | None
    status: str


class RoundMetrics(BaseModel):
    filters: dict[str, str | None]
    items: int
    acceptance_rate: MetricValue
    estimated_review_hours: MetricValue
    in_competitive_band: MetricValue
    avg_gross_margin: MetricValue
    reversal_rate: MetricValue
    recommendation_distribution: dict[str, int]
    price_index_by_curve: dict[str, float | None]
    decisions_by_recommendation: dict[str, dict[str, int]]
    rejection_reasons: dict[str, int]
    top_value_at_stake: list[TopItem]
