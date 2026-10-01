"""Métricas da rodada, calculadas a partir das recomendações e das decisões registradas."""

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import DecisionType, RecommendationType
from app.repositories import recommendations as recs_repo
from app.repositories import rounds as rounds_repo
from app.repositories.recommendations import RecommendationRow
from app.schemas.metrics import MetricValue, RoundMetrics, TopItem
from app.services.decisions import REJECTION_REASONS
from app.services.errors import NotFoundError

ACCEPTANCE_TOLERANCE = Decimal("0.01")  # edição com ajuste ≤ 1% do preço atual conta como aceite


@dataclass
class Acceptance:
    numerator: int
    denominator: int

    @property
    def value(self) -> float | None:
        return self.numerator / self.denominator if self.denominator else None


def acceptance(rows: list[RecommendationRow]) -> Acceptance:
    """Aceite (métrica primária): sobre SUBIR/BAIXAR com decisão vigente diferente de ADIAR,
    conta APROVAR e EDITAR com |aplicado − sugerido| ≤ 1% do preço atual."""
    numerator = denominator = 0
    for row in rows:
        rec, last = row.recommendation, row.last_decision
        if rec.recommendation not in (RecommendationType.SUBIR, RecommendationType.BAIXAR):
            continue
        if last is None or last.decision == DecisionType.ADIAR:
            continue
        denominator += 1
        if last.decision == DecisionType.APROVAR:
            numerator += 1
        elif last.decision == DecisionType.EDITAR and last.applied_price is not None:
            if abs(last.applied_price - rec.suggested_price) <= (
                ACCEPTANCE_TOLERANCE * rec.current_price
            ):
                numerator += 1
    return Acceptance(numerator, denominator)


# --- Painel de métricas --------------------------------------------------------------------------

REVIEW_MINUTES_PER_ITEM = 2
COMPETITIVE_BAND = Decimal("0.02")
TARGETS = {
    "acceptance_rate": 0.70,
    "estimated_review_hours": 6,
    "in_competitive_band": 0.80,
    "avg_gross_margin": 0.325,
    "reversal_rate": 0.03,
}
DECISION_BUCKETS = ("APROVADA", "EDITADA", "REJEITADA", "ADIADA", "PENDENTE", "SEM_ACAO")


def _metric(value: float | None, target: float, **extra) -> MetricValue:
    return MetricValue(value=value, target=target, **extra)


def build_metrics(
    session: Session,
    round_id: uuid.UUID,
    *,
    channel: str | None = None,
    abc_curve: str | None = None,
) -> RoundMetrics:
    if rounds_repo.get(session, round_id) is None:
        raise NotFoundError("Rodada não encontrada.")
    rows = [
        r
        for r in recs_repo.all_for_round(session, round_id)
        if (channel is None or r.recommendation.channel == channel)
        and (abc_curve is None or r.recommendation.product.abc_curve == abc_curve)
    ]
    recs = [r.recommendation for r in rows]

    acc = acceptance(rows)
    decided = sum(1 for r in rows if r.status in recs_repo.DECIDED_STATUSES)

    priced = [r for r in recs if r.market_price]
    in_band = sum(
        1 for r in priced if abs(r.current_price / r.market_price - 1) <= COMPETITIVE_BAND
    )

    revenue = sum((r.est_monthly_revenue or Decimal(0)) for r in recs)
    weighted_margin = sum((r.est_monthly_revenue or Decimal(0)) * r.current_margin for r in recs)

    index_by_curve: dict[str, float | None] = {}
    for curve in ("A", "B", "C"):
        values = [
            float(r.current_price / r.market_price * 100)
            for r in priced
            if r.product.abc_curve == curve
        ]
        index_by_curve[curve] = round(sum(values) / len(values), 1) if values else None

    by_rec: dict[str, dict[str, int]] = {
        t.value: dict.fromkeys(DECISION_BUCKETS, 0) for t in RecommendationType
    }
    for row in rows:
        by_rec[row.recommendation.recommendation.value][row.status] += 1

    reasons = dict.fromkeys(REJECTION_REASONS, 0)
    for row in rows:
        last = row.last_decision
        if last is not None and last.decision == DecisionType.REJEITAR and last.rejection_reason:
            reasons[last.rejection_reason] = reasons.get(last.rejection_reason, 0) + 1

    top = sorted(
        (r for r in rows if r.value_at_stake is not None),
        key=lambda r: r.value_at_stake,
        reverse=True,
    )[:10]

    return RoundMetrics(
        filters={"channel": channel, "abc_curve": abc_curve},
        items=len(rows),
        acceptance_rate=_metric(
            acc.value,
            TARGETS["acceptance_rate"],
            numerator=acc.numerator,
            denominator=acc.denominator,
            note=None if acc.denominator else "nenhuma decisão registrada",
        ),
        estimated_review_hours=_metric(
            round(decided * REVIEW_MINUTES_PER_ITEM / 60, 2),
            TARGETS["estimated_review_hours"],
            numerator=decided,
            note="estimado: 2 min por item decidido",
        ),
        in_competitive_band=_metric(
            in_band / len(priced) if priced else None,
            TARGETS["in_competitive_band"],
            numerator=in_band,
            denominator=len(priced),
        ),
        avg_gross_margin=_metric(
            float(weighted_margin / revenue) if revenue else None,
            TARGETS["avg_gross_margin"],
        ),
        reversal_rate=_metric(None, TARGETS["reversal_rate"], note="não disponível na v1"),
        recommendation_distribution={
            t.value: sum(1 for r in recs if r.recommendation == t) for t in RecommendationType
        },
        price_index_by_curve=index_by_curve,
        decisions_by_recommendation=by_rec,
        rejection_reasons=reasons,
        top_value_at_stake=[
            TopItem(
                recommendation_id=r.recommendation.id,
                sku=r.recommendation.sku,
                product_name=r.recommendation.product.name,
                channel=r.recommendation.channel.value,
                recommendation=r.recommendation.recommendation.value,
                variation=float(r.recommendation.variation),
                value_at_stake=r.value_at_stake,
                status=r.status,
            )
            for r in top
        ],
    )
