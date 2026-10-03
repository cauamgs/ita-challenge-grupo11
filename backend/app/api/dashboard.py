import uuid

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.dashboard import Dashboard
from app.services import dashboard as dashboard_service

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=Dashboard, summary="Painel inicial da plataforma")
def get_dashboard(session: SessionDep, round_id: uuid.UUID | None = None) -> Dashboard:
    return dashboard_service.build(session, round_id)
