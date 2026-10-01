from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Product, ProductChannelState, StockSnapshot


def existing_skus(session: Session, skus: Iterable[str]) -> set[str]:
    return set(session.scalars(select(Product.sku).where(Product.sku.in_(set(skus)))))


def insert_products(session: Session, rows: list[dict]) -> None:
    if rows:
        session.execute(insert(Product).values(rows).on_conflict_do_nothing(index_elements=["sku"]))


def insert_channel_states(session: Session, rows: list[dict]) -> None:
    if rows:
        session.execute(
            insert(ProductChannelState)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["sku", "channel", "reference_date"])
        )


def insert_stock(session: Session, rows: list[dict]) -> None:
    if rows:
        session.execute(
            insert(StockSnapshot)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["sku", "reference_date"])
        )
