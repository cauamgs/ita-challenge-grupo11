import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.engine import CsvImportEngine, CsvValidationError, RecommendationEngine
from app.models import Recommendation, RecommendationType, Round
from app.models.enums import CHANNEL_LABELS, Channel
from app.repositories import products as products_repo
from app.repositories import recommendations as recs_repo
from app.repositories import rounds as rounds_repo
from app.repositories import users as users_repo
from app.schemas.rounds import RoundCounts, RoundOut, RoundSummary, TopValueAtStake
from app.services.errors import ConflictError, NotFoundError, ValidationFailed


def run_engine(
    session: Session,
    engine: RecommendationEngine,
    round_date: date,
    *,
    source_file: str | None = None,
    user_id: uuid.UUID | None = None,
    replace: bool = False,
) -> Round:
    """Executa um motor e grava a rodada. Não faz commit (quem chama decide)."""
    if user_id is not None and users_repo.get(session, user_id) is None:
        raise NotFoundError("Usuário não encontrado.")

    existing = rounds_repo.get_by_date(session, round_date)
    if existing is not None:
        if not replace:
            raise ConflictError(f"Já existe uma rodada em {round_date:%d/%m/%Y}.")
        if rounds_repo.has_decisions(session, existing.id):
            raise ConflictError(
                f"A rodada de {round_date:%d/%m/%Y} já tem decisões registradas "
                "e não pode ser substituída."
            )
        rounds_repo.delete_round(session, existing.id)
        session.flush()

    try:
        items = engine.run(round_date)
    except CsvValidationError as exc:
        raise ValidationFailed("CSV inválido.", exc.errors) from exc

    known = products_repo.existing_skus(session, (i.sku for i in items))
    unknown = sorted({i.sku for i in items} - known)
    if unknown:
        raise ValidationFailed(
            "SKU(s) não cadastrado(s) na base de produtos.",
            [
                {"linha": None, "campo": "sku", "erro": f"SKU desconhecido: {sku}"}
                for sku in unknown
            ],
        )

    new_round = Round(
        round_date=round_date, source=engine.source, source_file=source_file, imported_by=user_id
    )
    new_round.recommendations = [
        Recommendation(**item.model_dump(exclude={"product_name", "category", "abc_curve"}))
        for item in items
    ]
    session.add(new_round)
    session.flush()
    return new_round


def import_csv(
    session: Session,
    content: bytes,
    *,
    filename: str | None = None,
    user_id: uuid.UUID | None = None,
    replace: bool = False,
) -> Round:
    engine = CsvImportEngine(content, filename)
    try:
        round_date = engine.detect_round_date()
    except CsvValidationError as exc:
        raise ValidationFailed("CSV inválido.", exc.errors) from exc
    return run_engine(
        session, engine, round_date, source_file=filename, user_id=user_id, replace=replace
    )


# --- Leitura -------------------------------------------------------------------------------------

REASON_GROUPS = ("campanha", "cobertura_curta", "dados_frageis", "outros")


def reason_group(reason: str) -> str:
    """Agrupa um motivo de revisão por palavra-chave (ESPECIFICACAO_V1 §3.2)."""
    text = reason.lower()
    if "campanha" in text:
        return "campanha"
    if "cobertura" in text:
        return "cobertura_curta"
    if "dados" in text or "confiança" in text:
        return "dados_frageis"
    return "outros"


def count_review_reasons(recs: list[Recommendation]) -> dict[str, int]:
    """Cada REVISAR conta uma vez em cada grupo presente nos seus motivos (DECISOES D05)."""
    counts = dict.fromkeys(REASON_GROUPS, 0)
    for rec in recs:
        if rec.recommendation != RecommendationType.REVISAR:
            continue
        groups = {reason_group(r) for r in rec.review_reasons} or {"outros"}
        for group in groups:
            counts[group] += 1
    return counts


def _counts(recs: list[Recommendation]) -> dict[str, int]:
    counts = {"total": len(recs)} | {r.value: 0 for r in RecommendationType}
    for rec in recs:
        counts[rec.recommendation.value] += 1
    return counts


def list_rounds(session: Session) -> list[RoundOut]:
    return [
        RoundOut(
            id=r.id,
            round_date=r.round_date,
            source=r.source,
            created_at=r.created_at,
            counts=RoundCounts(**_counts(r.recommendations)),
        )
        for r in rounds_repo.list_all(session)
    ]


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def build_summary(session: Session, round_id: uuid.UUID) -> RoundSummary:
    round_ = rounds_repo.get(session, round_id)
    if round_ is None:
        raise NotFoundError("Rodada não encontrada.")
    rows = recs_repo.all_for_round(session, round_id)
    recs = [r.recommendation for r in rows]
    counts = _counts(recs)
    by_rec = {k: v for k, v in counts.items() if k != "total"}
    with_change = by_rec["SUBIR"] + by_rec["BAIXAR"]
    reasons = count_review_reasons(recs)
    requires_approval = sum(1 for r in recs if r.requires_approval)
    decided = sum(1 for r in rows if r.status in recs_repo.DECIDED_STATUSES)
    pending = sum(1 for r in rows if r.status in recs_repo.PENDING_STATUSES)

    # Maior valor em jogo entre as sugestões de alteração (SUBIR/BAIXAR) — DECISOES D12
    changes = [
        r
        for r in rows
        if r.recommendation.recommendation in (RecommendationType.SUBIR, RecommendationType.BAIXAR)
        and r.value_at_stake is not None
    ]
    top = max(changes, key=lambda r: r.value_at_stake, default=None)
    top_out = None
    if top is not None:
        rec = top.recommendation
        top_out = TopValueAtStake(
            recommendation_id=rec.id,
            sku=rec.sku,
            product=rec.product.name,
            channel=rec.channel.value,
            value=round(top.value_at_stake, 2),
        )

    reason_parts = [
        f"{reasons['campanha']} por campanha",
        f"{reasons['cobertura_curta']} por cobertura curta",
        f"{reasons['dados_frageis']} por dados frágeis",
    ]
    if reasons["outros"]:
        reason_parts.append(f"{reasons['outros']} por outros motivos")
    text = (
        f"{_plural(counts['total'], 'item', 'itens')} · "
        f"{with_change} com sugestão de alteração · "
        f"{by_rec['REVISAR']} {'exige' if by_rec['REVISAR'] == 1 else 'exigem'} revisão "
        f"({', '.join(reason_parts)}) · "
        f"{requires_approval} {'exige' if requires_approval == 1 else 'exigem'} aprovação."
    )
    if top_out is not None:
        text += (
            f" Maior valor em jogo: {top_out.sku} "
            f"{'na' if top_out.channel == Channel.LOJA_FISICA else 'no'} "
            f"{CHANNEL_LABELS[Channel(top_out.channel)]}."
        )

    return RoundSummary(
        round_id=round_.id,
        round_date=round_.round_date,
        total=counts["total"],
        with_change=with_change,
        by_recommendation=by_rec,
        review_reasons=reasons,
        requires_approval=requires_approval,
        top_value_at_stake=top_out,
        decided=decided,
        pending=pending,
        summary_text=text,
    )
