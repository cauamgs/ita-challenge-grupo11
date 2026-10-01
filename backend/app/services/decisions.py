"""Registro das decisões do analista. Append-only: só cria registros, nunca altera ou apaga."""

import csv
import io
import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Decision, DecisionType
from app.models.enums import CHANNEL_LABELS, Channel
from app.repositories import decisions as decisions_repo
from app.repositories import recommendations as recs_repo
from app.repositories import rounds as rounds_repo
from app.repositories import users as users_repo
from app.schemas.common import Page
from app.schemas.decisions import DecisionCreated, DecisionIn, HistoryItem
from app.services.errors import NotFoundError, ValidationFailed
from app.services.recommendations import decision_out, min_price_floor

REJECTION_REASONS = (
    "Discordo da referência de mercado",
    "Estoque/reposição",
    "Estratégia comercial",
    "Dados incorretos",
    "Outro",
)
MAX_VARIATION = Decimal("0.05")  # R02
CENT = Decimal("0.01")


def _brl(value: Decimal) -> str:
    text = f"{value.quantize(CENT, ROUND_HALF_UP):,.2f}"
    return "R$ " + text.replace(",", "_").replace(".", ",").replace("_", ".")


def price_warnings(rec, applied_price: Decimal) -> list[str]:
    """Avisos (não bloqueiam) para um preço editado: R01 (piso de margem) e R02 (variação > 5%)."""
    warnings = []
    floor = min_price_floor(rec)
    if applied_price < floor:
        warnings.append(f"Preço abaixo do piso de margem mínima ({_brl(floor)}) (R01)")
    variation = applied_price / rec.current_price - 1
    if abs(variation) > MAX_VARIATION:
        warnings.append("Variação acima de 5% em relação ao preço atual (R02)")
    return warnings


def create_decision(session: Session, rec_id: uuid.UUID, data: DecisionIn) -> DecisionCreated:
    row = recs_repo.get_row(session, rec_id)
    if row is None:
        raise NotFoundError("Recomendação não encontrada.")
    if users_repo.get(session, data.user_id) is None:
        raise NotFoundError("Usuário não encontrado.")
    rec = row.recommendation

    comment = (data.comment or "").strip() or None
    reason = None
    applied: Decimal | None = None
    warnings: list[str] = []

    if data.decision == DecisionType.APROVAR:
        applied = rec.suggested_price
    elif data.decision == DecisionType.EDITAR:
        if data.applied_price is None:
            raise ValidationFailed("Informe o novo preço para editar.")
        applied = Decimal(str(data.applied_price)).quantize(CENT, ROUND_HALF_UP)
        if applied <= 0:
            raise ValidationFailed("O preço deve ser maior que zero.")
        warnings = price_warnings(rec, applied)
    elif data.decision == DecisionType.REJEITAR:
        reason = (data.rejection_reason or "").strip()
        if not reason:
            raise ValidationFailed("Informe o motivo da rejeição.")
        if reason not in REJECTION_REASONS:
            raise ValidationFailed(f"Motivo de rejeição inválido: {reason}.")

    decision = Decision(
        recommendation_id=rec.id,
        user_id=data.user_id,
        decision=data.decision,
        applied_price=applied,
        rejection_reason=reason,
        comment=comment,
        snapshot_recommendation=rec.recommendation,
        snapshot_suggested_price=rec.suggested_price,
        snapshot_current_price=rec.current_price,
        created_at=datetime.now(UTC),  # DECISOES D14
    )
    session.add(decision)
    session.commit()
    session.refresh(decision)
    return DecisionCreated(decision=decision_out(decision), warnings=warnings)


EXPORT_COLUMNS = [
    "sku", "produto", "canal", "preco_atual", "preco_aplicado", "variacao", "decisao",
    "analista", "data_hora", "comentario",
]  # fmt: skip


def export_round(session: Session, round_id: uuid.UUID) -> tuple[str, str]:
    """CSV das decisões vigentes APROVAR/EDITAR da rodada. Devolve (nome do arquivo, conteúdo)."""
    round_ = rounds_repo.get(session, round_id)
    if round_ is None:
        raise NotFoundError("Rodada não encontrada.")
    tz = ZoneInfo(settings.timezone)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(EXPORT_COLUMNS)
    for row in recs_repo.all_for_round(session, round_id):
        last = row.last_decision
        if last is None or last.decision not in (DecisionType.APROVAR, DecisionType.EDITAR):
            continue
        rec = row.recommendation
        variation = (last.applied_price / rec.current_price - 1).quantize(Decimal("0.0001"))
        writer.writerow(
            [
                rec.sku,
                rec.product.name,
                CHANNEL_LABELS[rec.channel],
                f"{rec.current_price:.2f}",
                f"{last.applied_price:.2f}",
                f"{variation:.4f}",
                last.decision.value,
                last.user.name,
                last.created_at.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
                last.comment or "",
            ]
        )
    stamp = datetime.now(tz).strftime("%Y-%m-%d_%H%M")
    return f"decisoes_{round_.round_date.isoformat()}_{stamp}.csv", buffer.getvalue()


# --- Histórico -----------------------------------------------------------------------------------


def _day_bounds(tz: ZoneInfo, date_from: date | None, date_to: date | None):
    start = datetime.combine(date_from, time.min, tz) if date_from else None
    end = datetime.combine(date_to + timedelta(days=1), time.min, tz) if date_to else None
    return start, end


def history_item(decision: Decision) -> HistoryItem:
    rec = decision.recommendation
    return HistoryItem(
        **decision_out(decision).model_dump(),
        sku=rec.sku,
        product_name=rec.product.name,
        channel=rec.channel.value,
    )


def list_history(
    session: Session,
    *,
    user_id: uuid.UUID | None = None,
    decision: DecisionType | None = None,
    channel: Channel | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int | None = 25,
) -> Page[HistoryItem]:
    start, end = _day_bounds(ZoneInfo(settings.timezone), date_from, date_to)
    items, total = decisions_repo.search(
        session,
        user_id=user_id,
        decision=decision,
        channel=channel,
        created_from=start,
        created_to=end,
        page=page,
        page_size=page_size,
    )
    return Page(
        items=[history_item(d) for d in items],
        total=total,
        page=page,
        page_size=page_size or total,
    )


HISTORY_COLUMNS = [
    "data_hora", "analista", "rodada", "sku", "produto", "canal", "recomendacao",
    "preco_atual", "preco_sugerido", "decisao", "preco_aplicado", "motivo", "comentario",
]  # fmt: skip


def export_history(session: Session, **filters) -> tuple[str, str]:
    tz = ZoneInfo(settings.timezone)
    page = list_history(session, page_size=None, **filters)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(HISTORY_COLUMNS)
    for item in page.items:
        writer.writerow(
            [
                item.created_at.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
                item.user_name,
                item.round_date,
                item.sku,
                item.product_name,
                CHANNEL_LABELS[Channel(item.channel)],
                item.snapshot_recommendation,
                f"{item.snapshot_current_price:.2f}",
                f"{item.snapshot_suggested_price:.2f}",
                item.decision,
                f"{item.applied_price:.2f}" if item.applied_price is not None else "",
                item.rejection_reason or "",
                item.comment or "",
            ]
        )
    stamp = datetime.now(tz).strftime("%Y-%m-%d_%H%M")
    return f"historico_decisoes_{stamp}.csv", buffer.getvalue()
