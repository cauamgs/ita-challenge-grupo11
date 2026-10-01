import uuid
from typing import Literal

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.models import Channel
from app.schemas.metrics import RoundMetrics
from app.services import metrics as metrics_service

router = APIRouter(tags=["Métricas"])


@router.get(
    "/rounds/{round_id}/metrics",
    response_model=RoundMetrics,
    summary="Indicadores da rodada e da carteira (reflete as decisões registradas)",
)
def round_metrics(
    round_id: uuid.UUID,
    session: SessionDep,
    channel: Channel | None = None,
    abc_curve: Literal["A", "B", "C"] | None = None,
) -> RoundMetrics:
    return metrics_service.build_metrics(session, round_id, channel=channel, abc_curve=abc_curve)
