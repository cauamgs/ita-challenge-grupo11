"""Histórico de análises por analista: volume, tipo de decisão, aceite pessoal e atividade."""

import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Decision, DecisionType, RecommendationType, User
from app.repositories import users as users_repo
from app.schemas.analysts import AnalystDetail, AnalystSummary, DayCount
from app.services.errors import NotFoundError

TOLERANCE = Decimal("0.01")


def _decisions(session: Session, user_id: uuid.UUID | None = None) -> list[Decision]:
    query = select(Decision).order_by(Decision.created_at)
    if user_id is not None:
        query = query.where(Decision.user_id == user_id)
    return list(session.scalars(query).unique())


def _accepted(d: Decision) -> bool:
    if d.decision == DecisionType.APROVAR:
        return True
    return (
        d.decision == DecisionType.EDITAR
        and d.applied_price is not None
        and abs(d.applied_price - d.snapshot_suggested_price)
        <= TOLERANCE * d.snapshot_current_price
    )


def _summary(user: User, decisions: list[Decision], now: datetime) -> AnalystSummary:
    """Aceite pessoal: sobre os registros do analista em SUBIR/BAIXAR (sem ADIAR)."""
    base = [
        d
        for d in decisions
        if d.snapshot_recommendation in (RecommendationType.SUBIR, RecommendationType.BAIXAR)
        and d.decision != DecisionType.ADIAR
    ]
    by_decision = Counter(d.decision.value for d in decisions)
    return AnalystSummary(
        id=user.id,
        name=user.name,
        role=user.role.value,
        decisions_total=len(decisions),
        by_decision={t.value: by_decision.get(t.value, 0) for t in DecisionType},
        acceptance_rate=sum(_accepted(d) for d in base) / len(base) if base else None,
        acceptance_base=len(base),
        rounds_count=len({d.recommendation.round_id for d in decisions}),
        decisions_last_7_days=sum(1 for d in decisions if d.created_at >= now - timedelta(days=7)),
        last_activity_at=decisions[-1].created_at if decisions else None,
    )


def list_analysts(session: Session) -> list[AnalystSummary]:
    now = datetime.now(UTC)
    by_user: dict[uuid.UUID, list[Decision]] = {}
    for d in _decisions(session):
        by_user.setdefault(d.user_id, []).append(d)
    return [_summary(u, by_user.get(u.id, []), now) for u in users_repo.list_active(session)]


def decisions_by_day(decisions: list[Decision], days: int, now: datetime) -> list[DayCount]:
    tz = ZoneInfo(settings.timezone)
    today = now.astimezone(tz).date()
    counts = Counter(d.created_at.astimezone(tz).date() for d in decisions)
    return [
        DayCount(date=day, count=counts.get(day, 0))
        for day in (today - timedelta(days=i) for i in range(days - 1, -1, -1))
    ]


def get_analyst(session: Session, user_id: uuid.UUID, days: int = 30) -> AnalystDetail:
    user = users_repo.get(session, user_id)
    if user is None:
        raise NotFoundError("Analista não encontrado.")
    now = datetime.now(UTC)
    decisions = _decisions(session, user_id)
    rejection = Counter(
        d.rejection_reason for d in decisions if d.decision == DecisionType.REJEITAR
    )
    return AnalystDetail(
        **_summary(user, decisions, now).model_dump(),
        decisions_by_day=decisions_by_day(decisions, days, now),
        by_recommendation={
            t.value: sum(1 for d in decisions if d.snapshot_recommendation == t)
            for t in RecommendationType
        },
        rejection_reasons=dict(rejection),
    )
