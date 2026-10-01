import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, uuid_pk
from app.models.catalog import Product
from app.models.enums import (
    Channel,
    RecommendationType,
    RiskLevel,
    channel_t,
    recommendation_t,
    risk_t,
)


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[uuid.UUID] = uuid_pk()
    round_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_file: Mapped[str | None] = mapped_column(Text)
    imported_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = created_at_col()

    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="round", cascade="all, delete-orphan", passive_deletes=True
    )


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint("round_id", "sku", "channel"),
        Index("ix_recommendations_round_priority", "round_id", "priority"),
        Index("ix_recommendations_round_recommendation", "round_id", "recommendation"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    round_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    sku: Mapped[str] = mapped_column(ForeignKey("products.sku"), nullable=False)
    channel: Mapped[Channel] = mapped_column(channel_t, nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    market_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    lowest_valid_competitor: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_margin: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    min_margin: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    target_margin: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    net_margin: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    stock_qty: Mapped[int | None] = mapped_column(Integer)
    coverage_days: Mapped[Decimal | None] = mapped_column(Numeric(8, 1))
    sales_trend_month: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sales_var_12m: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    recommendation: Mapped[RecommendationType] = mapped_column(recommendation_t, nullable=False)
    suggested_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    variation: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    resulting_margin: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(risk_t, nullable=False)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    data_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 3))
    requires_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    est_monthly_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    est_monthly_impact: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    review_reasons: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    data_alerts: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    created_at: Mapped[datetime] = created_at_col()

    round: Mapped[Round] = relationship(back_populates="recommendations")
    product: Mapped[Product] = relationship(lazy="joined")
