import uuid
from datetime import UTC, datetime, time

from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.api.deps import SessionDep
from app.models import SyncTrigger
from app.repositories import users as users_repo
from app.schemas.common import Page
from app.schemas.erp import (
    ErpStatus,
    ScheduleIn,
    ScheduleOut,
    SchedulePreview,
    SyncRequest,
    SyncRunOut,
)
from app.services import erp_schedule, erp_sync, erp_views
from app.services.errors import NotFoundError, ValidationFailed

router = APIRouter(prefix="/erp", tags=["Integração ERP"])
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def _check_user(session, user_id) -> None:
    if user_id is not None and users_repo.get(session, user_id) is None:
        raise NotFoundError("Usuário não encontrado.")


def _time(text: str) -> time:
    hour, minute = text.split(":")
    return time(int(hour), int(minute))


@router.get("/status", response_model=ErpStatus, summary="Situação da integração com o ERP")
def erp_status(session: SessionDep) -> ErpStatus:
    return erp_views.status(session)


@router.post(
    "/sync",
    response_model=SyncRunOut,
    status_code=status.HTTP_201_CREATED,
    summary="Sincroniza agora com o ERP (simulado)",
)
def sync_now(body: SyncRequest, session: SessionDep) -> SyncRunOut:
    _check_user(session, body.user_id)
    run = erp_sync.run_sync(session, trigger=SyncTrigger.MANUAL, user_id=body.user_id)
    return erp_views.run_out(run)


@router.post(
    "/import",
    response_model=SyncRunOut,
    status_code=status.HTTP_201_CREATED,
    summary="Importa um arquivo exportado do ERP (.xlsx no layout da base)",
)
async def import_file(
    session: SessionDep,
    file: UploadFile = File(..., description="Planilha .xlsx com as abas do ERP"),
    user_id: str | None = Form(None),
) -> SyncRunOut:
    content = await file.read()
    if not content:
        raise ValidationFailed("O arquivo está vazio.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValidationFailed("Arquivo maior que 20 MB.")
    uid = None
    if user_id:
        try:
            uid = uuid.UUID(user_id)
        except ValueError as exc:
            raise ValidationFailed("Usuário inválido.") from exc
        _check_user(session, uid)
    run = erp_sync.run_sync(
        session,
        trigger=SyncTrigger.ARQUIVO,
        content=content,
        source=f"Arquivo · {file.filename or 'sem nome'}",
        user_id=uid,
    )
    return erp_views.run_out(run)


@router.get("/syncs", response_model=Page[SyncRunOut], summary="Histórico de sincronizações")
def list_syncs(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[SyncRunOut]:
    return erp_views.list_runs(session, page, page_size)


@router.get(
    "/schedule", response_model=ScheduleOut, summary="Configuração da sincronização automática"
)
def get_schedule(session: SessionDep) -> ScheduleOut:
    return erp_views.schedule_out(erp_schedule.get_schedule(session))


@router.put("/schedule", response_model=ScheduleOut, summary="Salva a sincronização automática")
def put_schedule(body: ScheduleIn, session: SessionDep) -> ScheduleOut:
    _check_user(session, body.user_id)
    schedule = erp_schedule.update_schedule(
        session,
        enabled=body.enabled,
        frequency=body.frequency,
        time_of_day=_time(body.time_of_day),
        weekday=body.weekday,
        day_of_month=body.day_of_month,
        user_id=body.user_id,
    )
    return erp_views.schedule_out(schedule)


@router.post(
    "/schedule/preview",
    response_model=SchedulePreview,
    summary="Mostra quando seria a próxima execução, sem salvar",
)
def preview_schedule(body: ScheduleIn) -> SchedulePreview:
    erp_schedule.validate(body.frequency, body.weekday, body.day_of_month)
    when = _time(body.time_of_day)
    return SchedulePreview(
        description=erp_schedule.describe(body.frequency, when, body.weekday, body.day_of_month),
        next_run_at=erp_schedule.compute_next_run(
            body.frequency,
            when,
            datetime.now(UTC),
            weekday=body.weekday,
            day_of_month=body.day_of_month,
        ),
    )
