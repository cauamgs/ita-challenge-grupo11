import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import SessionDep
from app.models import Channel, DecisionType
from app.schemas.common import Page
from app.schemas.decisions import DecisionCreated, DecisionIn, HistoryItem
from app.services import decisions as decisions_service

router = APIRouter(tags=["Decisões"])


def csv_response(filename: str, content: str) -> Response:
    # BOM para o Excel reconhecer UTF-8 (acentos)
    return Response(
        content="﻿" + content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/recommendations/{rec_id}/decisions",
    response_model=DecisionCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma decisão (sempre cria um novo registro)",
)
def create_decision(rec_id: uuid.UUID, body: DecisionIn, session: SessionDep) -> DecisionCreated:
    return decisions_service.create_decision(session, rec_id, body)


@router.get(
    "/rounds/{round_id}/export",
    summary="Exporta em CSV as decisões vigentes Aprovar/Editar da rodada",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_round(round_id: uuid.UUID, session: SessionDep) -> Response:
    return csv_response(*decisions_service.export_round(session, round_id))


def _history_filters(
    user_id: uuid.UUID | None = None,
    decision: DecisionType | None = None,
    channel: Channel | None = None,
    date_from: date | None = Query(None, description="Data inicial (AAAA-MM-DD), inclusive"),
    date_to: date | None = Query(None, description="Data final (AAAA-MM-DD), inclusive"),
) -> dict:
    return {
        "user_id": user_id,
        "decision": decision,
        "channel": channel,
        "date_from": date_from,
        "date_to": date_to,
    }


HistoryFilters = Annotated[dict, Depends(_history_filters)]


@router.get(
    "/decisions",
    response_model=Page[HistoryItem],
    summary="Histórico de decisões de todas as rodadas (mais recente primeiro)",
)
def list_decisions(
    session: SessionDep,
    filters: HistoryFilters,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> Page[HistoryItem]:
    return decisions_service.list_history(session, page=page, page_size=page_size, **filters)


@router.get(
    "/decisions/export",
    summary="Exporta o histórico de decisões em CSV (mesmos filtros)",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_decisions(session: SessionDep, filters: HistoryFilters) -> Response:
    return csv_response(*decisions_service.export_history(session, **filters))
