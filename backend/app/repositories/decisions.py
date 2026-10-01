from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Decision, Recommendation
from app.models.enums import Channel


def history_for_item(session: Session, sku: str, channel: Channel) -> list[Decision]:
    """Todas as decisões de um SKU × canal, em todas as rodadas, mais recente primeiro."""
    return list(
        session.scalars(
            select(Decision)
            .join(Recommendation, Recommendation.id == Decision.recommendation_id)
            .where(Recommendation.sku == sku, Recommendation.channel == channel)
            .order_by(Decision.created_at.desc())
        )
    )


def search(
    session: Session,
    *,
    user_id=None,
    decision=None,
    channel=None,
    created_from=None,
    created_to=None,
    page: int = 1,
    page_size: int | None = 25,
) -> tuple[list[Decision], int]:
    """Todas as decisões (todas as rodadas), mais recente primeiro. page_size=None: sem limite."""
    query = select(Decision).join(Recommendation, Recommendation.id == Decision.recommendation_id)
    if user_id is not None:
        query = query.where(Decision.user_id == user_id)
    if decision is not None:
        query = query.where(Decision.decision == decision)
    if channel is not None:
        query = query.where(Recommendation.channel == channel)
    if created_from is not None:
        query = query.where(Decision.created_at >= created_from)
    if created_to is not None:
        query = query.where(Decision.created_at < created_to)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    query = query.order_by(Decision.created_at.desc())
    if page_size is not None:
        query = query.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(query).unique()), total
