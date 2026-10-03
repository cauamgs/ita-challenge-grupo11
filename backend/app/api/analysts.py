import uuid

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.schemas.analysts import AnalystDetail, AnalystSummary
from app.services import analysts as analysts_service

router = APIRouter(prefix="/analysts", tags=["Analistas"])


@router.get("", response_model=list[AnalystSummary], summary="Resumo das análises por analista")
def list_analysts(session: SessionDep) -> list[AnalystSummary]:
    return analysts_service.list_analysts(session)


@router.get("/{user_id}", response_model=AnalystDetail, summary="Histórico de análises do analista")
def get_analyst(
    user_id: uuid.UUID, session: SessionDep, days: int = Query(30, ge=7, le=180)
) -> AnalystDetail:
    return analysts_service.get_analyst(session, user_id, days)
