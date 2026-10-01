"""Ponto de extensão do motor de decisão.

Na v1 a única implementação é `CsvImportEngine`, que lê a saída de uma rodada já calculada.
Na v2 o motor real implementa o mesmo protocolo e o restante do sistema não muda.
"""

from datetime import date
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, Field

from app.models.enums import Channel, RecommendationType, RiskLevel


class RecommendationIn(BaseModel):
    """Uma recomendação produzida pelo motor para um SKU × canal."""

    priority: int
    sku: str
    product_name: str
    category: str
    abc_curve: str
    channel: Channel
    current_price: Decimal
    market_price: Decimal | None = None
    lowest_valid_competitor: Decimal | None = None
    cost: Decimal
    current_margin: Decimal
    min_margin: Decimal
    target_margin: Decimal
    net_margin: Decimal | None = None
    stock_qty: int | None = None
    coverage_days: Decimal | None = None
    sales_trend_month: Decimal | None = None
    sales_var_12m: Decimal | None = None
    recommendation: RecommendationType
    suggested_price: Decimal
    variation: Decimal
    resulting_margin: Decimal
    risk_level: RiskLevel
    risk_score: Decimal | None = None
    data_confidence: Decimal | None = None
    requires_approval: bool = False
    est_monthly_revenue: Decimal | None = None
    est_monthly_impact: Decimal | None = None
    justification: str
    review_reasons: list[str] = Field(default_factory=list)
    data_alerts: list[str] = Field(default_factory=list)


class RecommendationEngine(Protocol):
    #: valor gravado em `rounds.source` ('csv_import' | 'engine')
    source: str

    def run(self, round_date: date) -> list[RecommendationIn]: ...
