"""Painel inicial: visão consolidada da rodada, da carteira, do ERP e da atividade dos analistas."""

from collections import Counter
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Decision, ErpSyncRun, PriceChangeType, PriceHistory, RiskLevel
from app.models.enums import CHANNEL_LABELS
from app.repositories import recommendations as recs_repo
from app.repositories import rounds as rounds_repo
from app.schemas.dashboard import (
    ActivityItem,
    AnalystActivity,
    Dashboard,
    ErpSummary,
    MonthChanges,
    RoundKpis,
    RoundProgress,
)
from app.services import analysts as analysts_service
from app.services import erp_views
from app.services import metrics as metrics_service
from app.services import rounds as rounds_service

TRIGGER_LABEL = {"INICIAL": "carga inicial", "MANUAL": "manual", "AGENDADO": "automática",
                 "ARQUIVO": "arquivo"}  # fmt: skip
SYNC_STATUS_LABEL = {"SUCESSO": "concluída", "ERRO": "com erro", "EM_ANDAMENTO": "em andamento"}
DECISION_VERB = {"APROVAR": "aprovou", "EDITAR": "editou", "REJEITAR": "rejeitou", "ADIAR": "adiou"}


def _months_back(today: date, n: int) -> list[str]:
    months, year, month = [], today.year, today.month
    for _ in range(n):
        months.append(f"{year:04d}-{month:02d}")
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    return list(reversed(months))


def build(session: Session, round_id=None) -> Dashboard:
    now = datetime.now(UTC)
    rounds = rounds_repo.list_all(session)
    current = next((r for r in rounds if r.id == round_id), rounds[0] if rounds else None)

    progress = kpis = None
    top_pending = []
    if current is not None:
        rows = recs_repo.all_for_round(session, current.id)
        summary = rounds_service.build_summary(session, current.id)
        pending_rows = [r for r in rows if r.status in recs_repo.PENDING_STATUSES]
        progress = RoundProgress(
            round_id=current.id,
            round_date=current.round_date,
            total=summary.total,
            with_change=summary.with_change,
            by_recommendation=summary.by_recommendation,
            decided=summary.decided,
            pending=summary.pending,
            postponed=sum(1 for r in rows if r.status == recs_repo.STATUS_ADIADA),
            no_action=sum(1 for r in rows if r.status == recs_repo.STATUS_SEM_ACAO),
            requires_approval_pending=sum(
                1 for r in pending_rows if r.recommendation.requires_approval
            ),
            high_risk_pending=sum(
                1 for r in pending_rows if r.recommendation.risk_level == RiskLevel.ALTO
            ),
            summary_text=summary.summary_text,
        )
        metrics = metrics_service.build_metrics(session, current.id)
        kpis = RoundKpis(
            acceptance_rate=metrics.acceptance_rate,
            estimated_review_hours=metrics.estimated_review_hours,
            in_competitive_band=metrics.in_competitive_band,
            avg_gross_margin=metrics.avg_gross_margin,
        )
        top_pending = [t for t in metrics.top_value_at_stake if t.status in ("PENDENTE", "ADIADA")][
            :5
        ]

    # Alterações de preço vindas do ERP
    changes = list(
        session.scalars(
            select(PriceHistory).where(PriceHistory.change_type != PriceChangeType.INICIAL)
        )
    )
    today = now.date()
    per_month: dict[str, Counter] = {}
    for e in changes:
        per_month.setdefault(e.effective_date.strftime("%Y-%m"), Counter())[
            e.change_type.value
        ] += 1
    months = _months_back(today, 6)  # últimos 6 meses, incluindo o atual
    by_month = [
        MonthChanges(
            month=m,
            increases=per_month.get(m, Counter())["AUMENTO"],
            decreases=per_month.get(m, Counter())["REDUCAO"],
        )
        for m in months
    ]
    recent = [e for e in changes if e.effective_date >= today - timedelta(days=90)]
    changes_90d = {
        "AUMENTO": sum(1 for e in recent if e.change_type == PriceChangeType.AUMENTO),
        "REDUCAO": sum(1 for e in recent if e.change_type == PriceChangeType.REDUCAO),
    }

    # Atividade
    decisions = list(session.scalars(select(Decision).order_by(Decision.created_at)).unique())
    round_decisions = Counter(
        d.user_id for d in decisions if current and d.recommendation.round_id == current.id
    )
    analysts = [
        AnalystActivity(
            id=a.id,
            name=a.name,
            role=a.role,
            decisions_total=a.decisions_total,
            decisions_round=round_decisions.get(a.id, 0),
        )
        for a in analysts_service.list_analysts(session)
    ]
    activity = [
        ActivityItem(
            kind="DECISAO",
            at=d.created_at,
            title=f"{d.user.name} {DECISION_VERB[d.decision.value]} "
            f"{d.recommendation.sku} · {CHANNEL_LABELS[d.recommendation.channel]}",
            detail=d.rejection_reason or d.comment,
            user_name=d.user.name,
            link=f"/recomendacoes?item={d.recommendation_id}",
        )
        for d in decisions[-8:]
    ]
    for run in session.scalars(select(ErpSyncRun).order_by(ErpSyncRun.started_at.desc()).limit(4)):
        activity.append(
            ActivityItem(
                kind="SYNC",
                at=run.started_at,
                title=f"Sincronização com o ERP ({TRIGGER_LABEL[run.trigger.value]}): "
                f"{SYNC_STATUS_LABEL[run.status.value]}",
                detail=run.message,
                user_name=run.user.name if run.user else None,
                link="/erp",
            )
        )
    activity.sort(key=lambda a: a.at, reverse=True)

    status = erp_views.status(session)
    return Dashboard(
        round=progress,
        kpis=kpis,
        top_pending=top_pending,
        erp=ErpSummary(
            last_sync=status.last_sync,
            schedule=status.schedule,
            products=status.products,
            last_reference_date=status.last_reference_date,
        ),
        price_changes_by_month=by_month,
        price_changes_90d=changes_90d,
        decisions_by_day=analysts_service.decisions_by_day(decisions, 14, now),
        analysts=analysts,
        recent_activity=activity[:10],
    )
