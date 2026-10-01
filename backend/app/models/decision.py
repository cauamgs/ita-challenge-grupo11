import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, uuid_pk
from app.models.enums import (
    DecisionType,
    RecommendationType,
    decision_t,
    recommendation_t,
)
from app.models.round import Recommendation
from app.models.user import User


class Decision(Base):
    """Decisão do analista. Append-only: um trigger da migration bloqueia UPDATE/DELETE."""

    __tablename__ = "decisions"
    __table_args__ = (
        Index("ix_decisions_recommendation_created", "recommendation_id", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    decision: Mapped[DecisionType] = mapped_column(decision_t, nullable=False)
    applied_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    snapshot_recommendation: Mapped[RecommendationType] = mapped_column(
        recommendation_t, nullable=False
    )
    snapshot_suggested_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    snapshot_current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = created_at_col()

    recommendation: Mapped[Recommendation] = relationship(lazy="joined")
    user: Mapped[User] = relationship(lazy="joined")
