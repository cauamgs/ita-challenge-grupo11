"""Catálogo de produtos (vindo do ERP) e histórico de preço por SKU."""

from collections import Counter
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    PriceChangeType,
    PriceHistory,
    Product,
    ProductChannelState,
    Recommendation,
    Round,
    StockSnapshot,
)
from app.repositories import recommendations as recs_repo
from app.repositories import rounds as rounds_repo
from app.schemas.common import Page
from app.schemas.products import (
    ChannelPrice,
    ChannelState,
    PriceEventOut,
    ProductDetail,
    ProductListItem,
    ProductRecommendation,
    StockOut,
)
from app.services.errors import NotFoundError
from app.services.recommendations import decision_out

CHANNEL_ORDER = {"LOJA_FISICA": 0, "ECOMMERCE": 1, "MARKETPLACE": 2}


def event_out(e: PriceHistory) -> PriceEventOut:
    return PriceEventOut(
        id=e.id,
        sku=e.sku,
        channel=e.channel.value,
        effective_date=e.effective_date,
        old_price=float(e.old_price) if e.old_price is not None else None,
        new_price=float(e.new_price),
        variation=float(e.variation) if e.variation is not None else None,
        change_type=e.change_type.value,
        source=e.source,
        reason=e.reason,
        origin=e.origin,
        recorded_at=e.created_at,
    )


def _latest_states(session: Session, skus: list[str]) -> dict[str, list[ProductChannelState]]:
    rows = session.scalars(
        select(ProductChannelState)
        .where(ProductChannelState.sku.in_(skus))
        .distinct(ProductChannelState.sku, ProductChannelState.channel)
        .order_by(
            ProductChannelState.sku,
            ProductChannelState.channel,
            ProductChannelState.reference_date.desc(),
        )
    )
    out: dict[str, list[ProductChannelState]] = {}
    for r in rows:
        out.setdefault(r.sku, []).append(r)
    for states in out.values():
        states.sort(key=lambda s: CHANNEL_ORDER[s.channel.value])
    return out


def _latest_stock(session: Session, skus: list[str]) -> dict[str, StockSnapshot]:
    rows = session.scalars(
        select(StockSnapshot)
        .where(StockSnapshot.sku.in_(skus))
        .distinct(StockSnapshot.sku)
        .order_by(StockSnapshot.sku, StockSnapshot.reference_date.desc())
    )
    return {r.sku: r for r in rows}


def _pending_by_sku(session: Session) -> Counter:
    rounds = rounds_repo.list_all(session)
    if not rounds:
        return Counter()
    return Counter(
        r.recommendation.sku
        for r in recs_repo.all_for_round(session, rounds[0].id)
        if r.status in recs_repo.PENDING_STATUSES
    )


def categories(session: Session) -> list[str]:
    return list(session.scalars(select(Product.category).distinct().order_by(Product.category)))


def list_products(
    session: Session,
    *,
    q: str | None = None,
    category: str | None = None,
    abc_curve: str | None = None,
    status: str | None = None,
    changed: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> Page[ProductListItem]:
    changes = (
        select(
            PriceHistory.sku,
            func.count().label("n"),
            func.max(PriceHistory.effective_date).label("last"),
        )
        .where(PriceHistory.change_type != PriceChangeType.INICIAL)
        .group_by(PriceHistory.sku)
        .subquery()
    )
    query = select(Product, func.coalesce(changes.c.n, 0)).outerjoin(
        changes, changes.c.sku == Product.sku
    )
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Product.sku.ilike(pattern), Product.name.ilike(pattern)))
    if category:
        query = query.where(Product.category == category)
    if abc_curve:
        query = query.where(Product.abc_curve == abc_curve)
    if status:
        query = query.where(Product.status == status)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    if changed == "recentes":
        query = query.order_by(changes.c.last.desc().nulls_last(), Product.sku)
    else:
        query = query.order_by(Product.sku)
    rows = session.execute(query.offset((page - 1) * page_size).limit(page_size)).all()

    skus = [p.sku for p, _ in rows]
    states = _latest_states(session, skus)
    stock = _latest_stock(session, skus)
    last_changes = {
        e.sku: e
        for e in session.scalars(
            select(PriceHistory)
            .where(PriceHistory.sku.in_(skus), PriceHistory.change_type != PriceChangeType.INICIAL)
            .distinct(PriceHistory.sku)
            .order_by(
                PriceHistory.sku, PriceHistory.effective_date.desc(), PriceHistory.created_at.desc()
            )
        )
    }
    pending = _pending_by_sku(session)
    items = []
    for product, n_changes in rows:
        st = stock.get(product.sku)
        last = last_changes.get(product.sku)
        items.append(
            ProductListItem(
                sku=product.sku,
                name=product.name,
                category=product.category,
                brand=product.brand,
                abc_curve=product.abc_curve,
                status=product.status,
                prices=[
                    ChannelPrice(
                        channel=s.channel.value,
                        current_price=float(s.current_price),
                        reference_date=s.reference_date,
                    )
                    for s in states.get(product.sku, [])
                ],
                stock_qty=st.quantity if st else None,
                coverage_days=float(st.coverage_days)
                if st and st.coverage_days is not None
                else None,
                last_change=event_out(last) if last else None,
                price_changes=n_changes,
                pending_recommendations=pending.get(product.sku, 0),
            )
        )
    return Page(items=items, total=total, page=page, page_size=page_size)


def get_product(session: Session, sku: str) -> ProductDetail:
    product = session.get(Product, sku)
    if product is None:
        raise NotFoundError("Produto não encontrado.")
    states = _latest_states(session, [sku]).get(sku, [])
    stock = _latest_stock(session, [sku]).get(sku)
    events = session.scalars(
        select(PriceHistory)
        .where(PriceHistory.sku == sku)
        .order_by(PriceHistory.effective_date.desc(), PriceHistory.created_at.desc())
    )
    recs = session.scalars(
        select(Recommendation)
        .join(Round, Round.id == Recommendation.round_id)
        .where(Recommendation.sku == sku)
        .order_by(Round.round_date.desc(), Recommendation.channel)
    ).all()
    rec_items = []
    for rec in recs:
        row = recs_repo.get_row(session, rec.id)
        rec_items.append(
            ProductRecommendation(
                id=rec.id,
                round_date=rec.round.round_date,
                channel=rec.channel.value,
                recommendation=rec.recommendation.value,
                current_price=float(rec.current_price),
                suggested_price=float(rec.suggested_price),
                variation=float(rec.variation),
                risk_level=rec.risk_level.value,
                status=row.status,
                last_decision=decision_out(row.last_decision) if row.last_decision else None,
            )
        )
    return ProductDetail(
        sku=product.sku,
        name=product.name,
        category=product.category,
        brand=product.brand,
        abc_curve=product.abc_curve,
        status=product.status,
        is_strategic=product.is_strategic,
        channels=[
            ChannelState(
                channel=s.channel.value,
                current_price=float(s.current_price),
                reference_date=s.reference_date,
                replacement_cost=float(s.replacement_cost),
                taxes=float(s.taxes),
                freight=float(s.freight),
                channel_fee=float(s.channel_fee),
                min_margin=float(s.min_margin),
                target_margin=float(s.target_margin),
                min_price_floor=float(
                    (s.replacement_cost / (1 - s.min_margin)).quantize(Decimal("0.01"))
                ),
            )
            for s in states
        ],
        stock=StockOut(
            reference_date=stock.reference_date,
            quantity=stock.quantity,
            coverage_days=float(stock.coverage_days) if stock.coverage_days is not None else None,
            open_po_quantity=stock.open_po_quantity,
            expected_receipt=stock.expected_receipt,
            location=stock.location,
        )
        if stock
        else None,
        price_history=[event_out(e) for e in events],
        recommendations=rec_items,
    )
