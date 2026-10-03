import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.decisions import DecisionOut


class ChannelPrice(BaseModel):
    channel: str
    current_price: float
    reference_date: date


class PriceEventOut(BaseModel):
    id: uuid.UUID
    sku: str
    channel: str
    effective_date: date
    old_price: float | None
    new_price: float
    variation: float | None
    change_type: str
    source: str
    reason: str | None
    origin: str | None
    recorded_at: datetime


class ProductListItem(BaseModel):
    sku: str
    name: str
    category: str
    brand: str
    abc_curve: str
    status: str
    prices: list[ChannelPrice]
    stock_qty: int | None
    coverage_days: float | None
    last_change: PriceEventOut | None
    price_changes: int
    pending_recommendations: int


class ChannelState(BaseModel):
    channel: str
    current_price: float
    reference_date: date
    replacement_cost: float
    taxes: float
    freight: float
    channel_fee: float
    min_margin: float
    target_margin: float
    min_price_floor: float


class StockOut(BaseModel):
    reference_date: date
    quantity: int
    coverage_days: float | None
    open_po_quantity: int
    expected_receipt: date | None
    location: str | None


class ProductRecommendation(BaseModel):
    id: uuid.UUID
    round_date: date
    channel: str
    recommendation: str
    current_price: float
    suggested_price: float
    variation: float
    risk_level: str
    status: str
    last_decision: DecisionOut | None


class ProductDetail(BaseModel):
    sku: str
    name: str
    category: str
    brand: str
    abc_curve: str
    status: str
    is_strategic: bool
    channels: list[ChannelState]
    stock: StockOut | None
    price_history: list[PriceEventOut]
    recommendations: list[ProductRecommendation]
