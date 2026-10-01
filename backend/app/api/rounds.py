import uuid
from typing import Literal

from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.api.deps import SessionDep
from app.models import Channel, RecommendationType, RiskLevel
from app.repositories.recommendations import RecommendationFilters
from app.schemas.common import Page
from app.schemas.recommendations import RecommendationListItem
from app.schemas.rounds import ImportResult, RoundOut, RoundSummary
from app.services import recommendations as recs_service
from app.services import rounds as rounds_service
from app.services.errors import ValidationFailed

router = APIRouter(tags=["Rodadas"])


@router.get(
    "/rounds", response_model=list[RoundOut], summary="Lista rodadas (mais recente primeiro)"
)
def list_rounds(session: SessionDep) -> list[RoundOut]:
    return rounds_service.list_rounds(session)


@router.get("/rounds/{round_id}/summary", response_model=RoundSummary, summary="Resumo da rodada")
def round_summary(round_id: uuid.UUID, session: SessionDep) -> RoundSummary:
    return rounds_service.build_summary(session, round_id)


@router.get(
    "/rounds/{round_id}/recommendations",
    response_model=Page[RecommendationListItem],
    summary="Lista recomendações da rodada com filtros, ordenação e paginação",
)
def list_recommendations(
    round_id: uuid.UUID,
    session: SessionDep,
    channel: Channel | None = None,
    abc_curve: Literal["A", "B", "C"] | None = None,
    recommendation: RecommendationType | None = None,
    risk_level: RiskLevel | None = None,
    status: Literal["PENDENTE", "DECIDIDO"] | None = None,
    requires_approval: bool | None = None,
    q: str | None = Query(None, description="Busca por SKU ou nome do produto"),
    sort: Literal["priority", "variation", "value_at_stake", "risk"] = "priority",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> Page[RecommendationListItem]:
    filters = RecommendationFilters(
        channel=channel,
        abc_curve=abc_curve,
        recommendation=recommendation,
        risk_level=risk_level,
        status=status,
        requires_approval=requires_approval,
        q=q,
    )
    return recs_service.list_recommendations(
        session, round_id, filters, sort=sort, order=order, page=page, page_size=page_size
    )


@router.post(
    "/rounds/import",
    response_model=ImportResult,
    status_code=status.HTTP_201_CREATED,
    summary="Importa uma rodada a partir do CSV de recomendações",
    responses={
        409: {"description": "Já existe rodada nessa data (use replace=true)"},
        422: {"description": "CSV inválido; `errors` traz os erros por linha"},
    },
)
async def import_round(
    session: SessionDep,
    file: UploadFile = File(..., description="CSV no formato de recomendacoes_rodada_*.csv"),
    user_id: uuid.UUID | None = Form(None),
    replace: bool = Query(False),
) -> ImportResult:
    content = await file.read()
    if not content:
        raise ValidationFailed("O arquivo está vazio.")
    new_round = rounds_service.import_csv(
        session, content, filename=file.filename, user_id=user_id, replace=replace
    )
    session.commit()
    return ImportResult(
        round_id=new_round.id,
        round_date=new_round.round_date,
        imported=len(new_round.recommendations),
    )
