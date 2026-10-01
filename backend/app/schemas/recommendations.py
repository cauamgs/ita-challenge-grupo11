import uuid

from pydantic import BaseModel

from app.schemas.decisions import DecisionOut


class RecommendationListItem(BaseModel):
    id: uuid.UUID
    priority: int
    sku: str
    product_name: str
    category: str
    abc_curve: str
    channel: str
    current_price: float
    market_price: float | None
    recommendation: str
    suggested_price: float
    variation: float
    resulting_margin: float
    risk_level: str
    requires_approval: bool
    value_at_stake: float | None
    status: str
    last_decision: DecisionOut | None


class ProductOut(BaseModel):
    sku: str
    name: str
    category: str
    brand: str
    abc_curve: str
    status: str
    is_strategic: bool


class RecommendationDetail(RecommendationListItem):
    round_id: uuid.UUID
    round_date: str
    lowest_valid_competitor: float | None
    cost: float
    current_margin: float
    min_margin: float
    target_margin: float
    net_margin: float | None
    stock_qty: int | None
    coverage_days: float | None
    sales_trend_month: float | None
    sales_var_12m: float | None
    risk_score: float | None
    data_confidence: float | None
    est_monthly_revenue: float | None
    est_monthly_impact: float | None
    justification: str
    review_reasons: list[str]
    data_alerts: list[str]
    min_price_floor: float
    product: ProductOut
    decision_history: list[DecisionOut]
