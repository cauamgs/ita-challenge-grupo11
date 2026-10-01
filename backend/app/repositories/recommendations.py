"""Consultas de recomendações com a decisão vigente (a mais recente) de cada uma."""

import uuid
from dataclasses import dataclass

from sqlalchemy import ColumnElement, Select, and_, case, func, literal, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import Decision, DecisionType, Product, Recommendation, RecommendationType

# Status exibidos na lista (ver docs/DECISOES.md D11)
STATUS_PENDENTE = "PENDENTE"
STATUS_ADIADA = "ADIADA"
STATUS_SEM_ACAO = "SEM_ACAO"
DECISION_STATUS = {
    DecisionType.APROVAR: "APROVADA",
    DecisionType.EDITAR: "EDITADA",
    DecisionType.REJEITAR: "REJEITADA",
    DecisionType.ADIAR: STATUS_ADIADA,
}
PENDING_STATUSES = (STATUS_PENDENTE, STATUS_ADIADA)
DECIDED_STATUSES = ("APROVADA", "EDITADA", "REJEITADA")


def latest_decisions_subquery():
    return (
        select(Decision)
        .distinct(Decision.recommendation_id)
        .order_by(Decision.recommendation_id, Decision.created_at.desc())
        .subquery("latest_decision")
    )


def value_at_stake_expr() -> ColumnElement:
    return case(
        (Recommendation.recommendation == RecommendationType.MANTER, None),
        else_=Recommendation.est_monthly_revenue * func.abs(Recommendation.variation),
    )


def status_expr(last: type[Decision]) -> ColumnElement:
    whens = [
        (
            and_(last.id.is_(None), Recommendation.recommendation == RecommendationType.MANTER),
            literal(STATUS_SEM_ACAO),
        ),
        (last.id.is_(None), literal(STATUS_PENDENTE)),
    ]
    whens += [(last.decision == d, literal(s)) for d, s in DECISION_STATUS.items()]
    return case(*whens, else_=literal(STATUS_PENDENTE))


@dataclass
class RecommendationFilters:
    channel: str | None = None
    abc_curve: str | None = None
    recommendation: str | None = None
    risk_level: str | None = None
    status: str | None = None  # PENDENTE | DECIDIDO
    requires_approval: bool | None = None
    q: str | None = None


SORT_COLUMNS = ("priority", "variation", "value_at_stake", "risk")


@dataclass
class RecommendationRow:
    recommendation: Recommendation
    last_decision: Decision | None
    status: str
    value_at_stake: float | None


def _base_query(round_id: uuid.UUID) -> tuple[Select, type[Decision], ColumnElement, ColumnElement]:
    latest = latest_decisions_subquery()
    last = aliased(Decision, latest)
    status = status_expr(last).label("status")
    value = value_at_stake_expr().label("value_at_stake")
    query = (
        select(Recommendation, last, status, value)
        .join(Product, Product.sku == Recommendation.sku)
        .outerjoin(last, last.recommendation_id == Recommendation.id)
        .where(Recommendation.round_id == round_id)
    )
    return query, last, status, value


def list_for_round(
    session: Session,
    round_id: uuid.UUID,
    filters: RecommendationFilters,
    *,
    sort: str = "priority",
    order: str = "asc",
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[RecommendationRow], int]:
    query, _last, status, value = _base_query(round_id)
    f = filters
    if f.channel:
        query = query.where(Recommendation.channel == f.channel)
    if f.abc_curve:
        query = query.where(Product.abc_curve == f.abc_curve)
    if f.recommendation:
        query = query.where(Recommendation.recommendation == f.recommendation)
    if f.risk_level:
        query = query.where(Recommendation.risk_level == f.risk_level)
    if f.requires_approval is not None:
        query = query.where(Recommendation.requires_approval.is_(f.requires_approval))
    if f.status == "PENDENTE":
        query = query.where(status.in_(PENDING_STATUSES))
    elif f.status == "DECIDIDO":
        query = query.where(status.in_(DECIDED_STATUSES))
    if f.q:
        pattern = f"%{f.q.strip()}%"
        query = query.where(or_(Recommendation.sku.ilike(pattern), Product.name.ilike(pattern)))

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0

    desc = order == "desc"
    if sort == "variation":
        keys = [Recommendation.variation.desc() if desc else Recommendation.variation.asc()]
    elif sort == "value_at_stake":
        keys = [value.desc().nulls_last() if desc else value.asc().nulls_last()]
    elif sort == "risk":
        keys = [
            Recommendation.risk_level.desc() if desc else Recommendation.risk_level.asc(),
            Recommendation.risk_score.desc() if desc else Recommendation.risk_score.asc(),
        ]
    else:
        keys = [Recommendation.priority.desc() if desc else Recommendation.priority.asc()]
    keys.append(Recommendation.priority.asc())

    rows = session.execute(
        query.order_by(*keys).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return [_row(r) for r in rows], total


def all_for_round(session: Session, round_id: uuid.UUID) -> list[RecommendationRow]:
    query, *_ = _base_query(round_id)
    rows = session.execute(query.order_by(Recommendation.priority)).all()
    return [_row(r) for r in rows]


def get_row(session: Session, rec_id: uuid.UUID) -> RecommendationRow | None:
    rec = session.get(Recommendation, rec_id)
    if rec is None:
        return None
    query, *_ = _base_query(rec.round_id)
    row = session.execute(query.where(Recommendation.id == rec_id)).one()
    return _row(row)


def _row(row) -> RecommendationRow:
    rec, last, status, value = row
    return RecommendationRow(
        recommendation=rec,
        last_decision=last,
        status=status,
        value_at_stake=round(float(value), 2) if value is not None else None,
    )
