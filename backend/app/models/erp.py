"""Integração (simulada) com o ERP: execuções de sincronização, agenda e histórico de preços."""

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at_col, uuid_pk
from app.models.enums import (
    Channel,
    PriceChangeType,
    SyncFrequency,
    SyncStatus,
    SyncTrigger,
    channel_t,
    price_change_t,
    sync_frequency_t,
    sync_status_t,
    sync_trigger_t,
)
from app.models.user import User


class ErpSyncRun(Base):
    __tablename__ = "erp_sync_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    trigger: Mapped[SyncTrigger] = mapped_column(sync_trigger_t, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SyncStatus] = mapped_column(sync_status_t, nullable=False)
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reference_date: Mapped[date | None] = mapped_column(Date)
    products_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    products_new: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    products_updated: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    prices_changed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    history_imported: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    stock_updated: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    message: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User | None] = relationship(lazy="joined")


class ErpSyncSchedule(Base):
    """Configuração única (id = 1) da sincronização automática."""

    __tablename__ = "erp_sync_schedule"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_erp_sync_schedule_single_row"),
        CheckConstraint("weekday between 0 and 6", name="ck_erp_sync_schedule_weekday"),
        CheckConstraint("day_of_month between 1 and 28", name="ck_erp_sync_schedule_day"),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    frequency: Mapped[SyncFrequency] = mapped_column(sync_frequency_t, nullable=False)
    weekday: Mapped[int | None] = mapped_column(SmallInteger)  # 0 = segunda … 6 = domingo
    day_of_month: Mapped[int | None] = mapped_column(SmallInteger)
    time_of_day: Mapped[time] = mapped_column(Time, nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User | None] = relationship(lazy="joined")


class PriceHistory(Base):
    """Alterações de preço de um SKU em um canal (vindas do ERP)."""

    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_sku_date", "sku", "effective_date"),
        Index("ix_price_history_date", "effective_date"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    sku: Mapped[str] = mapped_column(ForeignKey("products.sku"), nullable=False)
    channel: Mapped[Channel] = mapped_column(channel_t, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    variation: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))  # new/old − 1
    change_type: Mapped[PriceChangeType] = mapped_column(price_change_t, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)  # ERP_HISTORICO | ERP_SYNC
    reason: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str | None] = mapped_column(Text)
    sync_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("erp_sync_runs.id")
    )
    created_at: Mapped[datetime] = created_at_col()
