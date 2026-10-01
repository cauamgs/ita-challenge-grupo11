import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.explain import get_explainer
from app.models import Decision, Recommendation
from app.repositories import decisions as decisions_repo
from app.repositories import recommendations as recs_repo
from app.repositories import rounds as rounds_repo
from app.repositories.recommendations import RecommendationFilters, RecommendationRow
from app.schemas.common import Page
from app.schemas.decisions import DecisionOut
from app.schemas.recommendations import ProductOut, RecommendationDetail, RecommendationListItem
from app.services.errors import NotFoundError


def _f(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def min_price_floor(rec: Recommendation) -> Decimal:
    """Piso de margem mínima (R01): custo / (1 − margem mínima). Usado só para avisos."""
    return (rec.cost / (1 - rec.min_margin)).quantize(Decimal("0.01"))


def decision_out(decision: Decision) -> DecisionOut:
    rec = decision.recommendation
    return DecisionOut(
        id=decision.id,
        recommendation_id=decision.recommendation_id,
        round_date=rec.round.round_date.isoformat() if rec is not None else None,
        user_id=decision.user_id,
        user_name=decision.user.name,
        decision=decision.decision.value,
        applied_price=_f(decision.applied_price),
        rejection_reason=decision.rejection_reason,
        comment=decision.comment,
        snapshot_recommendation=decision.snapshot_recommendation.value,
        snapshot_suggested_price=float(decision.snapshot_suggested_price),
        snapshot_current_price=float(decision.snapshot_current_price),
        created_at=decision.created_at,
    )


def list_item(row: RecommendationRow) -> RecommendationListItem:
    rec = row.recommendation
    return RecommendationListItem(
        id=rec.id,
        priority=rec.priority,
        sku=rec.sku,
        product_name=rec.product.name,
        category=rec.product.category,
        abc_curve=rec.product.abc_curve,
        channel=rec.channel.value,
        current_price=float(rec.current_price),
        market_price=_f(rec.market_price),
        recommendation=rec.recommendation.value,
        suggested_price=float(rec.suggested_price),
        variation=float(rec.variation),
        resulting_margin=float(rec.resulting_margin),
        risk_level=rec.risk_level.value,
        requires_approval=rec.requires_approval,
        value_at_stake=row.value_at_stake,
        status=row.status,
        last_decision=decision_out(row.last_decision) if row.last_decision else None,
    )


def list_recommendations(
    session: Session,
    round_id: uuid.UUID,
    filters: RecommendationFilters,
    *,
    sort: str,
    order: str,
    page: int,
    page_size: int,
) -> Page[RecommendationListItem]:
    if rounds_repo.get(session, round_id) is None:
        raise NotFoundError("Rodada não encontrada.")
    rows, total = recs_repo.list_for_round(
        session, round_id, filters, sort=sort, order=order, page=page, page_size=page_size
    )
    return Page(items=[list_item(r) for r in rows], total=total, page=page, page_size=page_size)


def get_detail(session: Session, rec_id: uuid.UUID) -> RecommendationDetail:
    row = recs_repo.get_row(session, rec_id)
    if row is None:
        raise NotFoundError("Recomendação não encontrada.")
    rec = row.recommendation
    product = rec.product
    history = decisions_repo.history_for_item(session, rec.sku, rec.channel)
    return RecommendationDetail(
        **list_item(row).model_dump(),
        round_id=rec.round_id,
        round_date=rec.round.round_date.isoformat(),
        lowest_valid_competitor=_f(rec.lowest_valid_competitor),
        cost=float(rec.cost),
        current_margin=float(rec.current_margin),
        min_margin=float(rec.min_margin),
        target_margin=float(rec.target_margin),
        net_margin=_f(rec.net_margin),
        stock_qty=rec.stock_qty,
        coverage_days=_f(rec.coverage_days),
        sales_trend_month=_f(rec.sales_trend_month),
        sales_var_12m=_f(rec.sales_var_12m),
        risk_score=_f(rec.risk_score),
        data_confidence=_f(rec.data_confidence),
        est_monthly_revenue=_f(rec.est_monthly_revenue),
        est_monthly_impact=_f(rec.est_monthly_impact),
        justification=get_explainer().explain(rec),
        review_reasons=rec.review_reasons,
        data_alerts=rec.data_alerts,
        min_price_floor=float(min_price_floor(rec)),
        product=ProductOut(
            sku=product.sku,
            name=product.name,
            category=product.category,
            brand=product.brand,
            abc_curve=product.abc_curve,
            status=product.status,
            is_strategic=product.is_strategic,
        ),
        decision_history=[decision_out(d) for d in history],
    )
