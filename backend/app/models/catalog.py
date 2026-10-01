import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at_col, uuid_pk
from app.models.enums import Channel, channel_t


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("abc_curve in ('A','B','C')", name="ck_products_abc_curve"),)

    sku: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str] = mapped_column(Text, nullable=False)
    abc_curve: Mapped[str] = mapped_column(String(1), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    is_strategic: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = created_at_col()


class ProductChannelState(Base):
    __tablename__ = "product_channel_state"
    __table_args__ = (UniqueConstraint("sku", "channel", "reference_date"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    sku: Mapped[str] = mapped_column(ForeignKey("products.sku"), nullable=False)
    channel: Mapped[Channel] = mapped_column(channel_t, nullable=False)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    replacement_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    taxes: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    freight: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    channel_fee: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, server_default="0")
    min_margin: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    target_margin: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)


class StockSnapshot(Base):
    __tablename__ = "stock_snapshot"
    __table_args__ = (UniqueConstraint("sku", "reference_date"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    sku: Mapped[str] = mapped_column(ForeignKey("products.sku"), nullable=False)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    coverage_days: Mapped[Decimal | None] = mapped_column(Numeric(8, 1))
    open_po_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    expected_receipt: Mapped[date | None] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(Text)
