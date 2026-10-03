"""Agenda da sincronização automática com o ERP (diária, semanal ou mensal em um dia fixo)."""

import uuid
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ErpSyncRun, ErpSyncSchedule, SyncFrequency, SyncTrigger
from app.services import erp_sync
from app.services.errors import ValidationFailed

WEEKDAYS = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira",
            "sábado", "domingo")  # fmt: skip
DEFAULT_TIME = time(6, 0)


def _tz() -> ZoneInfo:
    return ZoneInfo(settings.timezone)


def compute_next_run(
    frequency: SyncFrequency,
    time_of_day: time,
    after: datetime,
    *,
    weekday: int | None = None,
    day_of_month: int | None = None,
) -> datetime:
    """Próxima execução estritamente depois de `after`, no fuso da empresa."""
    local = after.astimezone(_tz())

    def at(day) -> datetime:
        return datetime.combine(day, time_of_day, tzinfo=_tz())

    if frequency == SyncFrequency.DIARIA:
        candidate = at(local.date())
        return candidate if candidate > local else at(local.date() + timedelta(days=1))
    if frequency == SyncFrequency.SEMANAL:
        ahead = (weekday - local.weekday()) % 7
        candidate = at(local.date() + timedelta(days=ahead))
        return candidate if candidate > local else candidate + timedelta(days=7)
    # MENSAL: dia 1–28 (existe em todos os meses)
    candidate = at(local.date().replace(day=day_of_month))
    if candidate > local:
        return candidate
    year, month = (local.year + 1, 1) if local.month == 12 else (local.year, local.month + 1)
    return at(local.date().replace(year=year, month=month, day=day_of_month))


def describe(
    frequency: SyncFrequency,
    time_of_day: time,
    weekday: int | None = None,
    day_of_month: int | None = None,
) -> str:
    hour = time_of_day.strftime("%H:%M")
    if frequency == SyncFrequency.DIARIA:
        return f"Todos os dias às {hour}"
    if frequency == SyncFrequency.SEMANAL:
        day = WEEKDAYS[weekday]
        prefix = "Todo" if weekday >= 5 else "Toda"
        return f"{prefix} {day} às {hour}"
    return f"Todo dia {day_of_month} do mês às {hour}"


def validate(frequency: SyncFrequency, weekday: int | None, day_of_month: int | None) -> None:
    if frequency == SyncFrequency.SEMANAL and (weekday is None or not 0 <= weekday <= 6):
        raise ValidationFailed("Escolha o dia da semana da sincronização.")
    if frequency == SyncFrequency.MENSAL and (day_of_month is None or not 1 <= day_of_month <= 28):
        raise ValidationFailed("Escolha um dia do mês entre 1 e 28.")


def get_schedule(session: Session) -> ErpSyncSchedule:
    schedule = session.get(ErpSyncSchedule, 1)
    if schedule is None:
        schedule = ErpSyncSchedule(
            id=1, enabled=False, frequency=SyncFrequency.DIARIA, time_of_day=DEFAULT_TIME
        )
        session.add(schedule)
        session.commit()
    return schedule


def update_schedule(
    session: Session,
    *,
    enabled: bool,
    frequency: SyncFrequency,
    time_of_day: time,
    weekday: int | None,
    day_of_month: int | None,
    user_id: uuid.UUID | None,
    now: datetime | None = None,
) -> ErpSyncSchedule:
    validate(frequency, weekday, day_of_month)
    now = now or datetime.now(UTC)
    schedule = get_schedule(session)
    schedule.enabled = enabled
    schedule.frequency = frequency
    schedule.time_of_day = time_of_day.replace(second=0, microsecond=0)
    schedule.weekday = weekday if frequency == SyncFrequency.SEMANAL else None
    schedule.day_of_month = day_of_month if frequency == SyncFrequency.MENSAL else None
    schedule.next_run_at = (
        compute_next_run(
            frequency, schedule.time_of_day, now, weekday=weekday, day_of_month=day_of_month
        )
        if enabled
        else None
    )
    schedule.updated_by = user_id
    schedule.updated_at = now
    session.commit()
    return schedule


def run_due_sync(session: Session, now: datetime | None = None) -> ErpSyncRun | None:
    """Roda a sincronização agendada se já passou da hora. Seguro com mais de um processo."""
    now = now or datetime.now(UTC)
    schedule = session.scalar(
        select(ErpSyncSchedule)
        .where(ErpSyncSchedule.id == 1)
        .with_for_update(skip_locked=True, of=ErpSyncSchedule)
    )
    if (
        schedule is None
        or not schedule.enabled
        or schedule.next_run_at is None
        or schedule.next_run_at > now
    ):
        session.rollback()
        return None
    # agenda a próxima antes de rodar, para não executar duas vezes
    schedule.last_run_at = now
    schedule.next_run_at = compute_next_run(
        schedule.frequency,
        schedule.time_of_day,
        now,
        weekday=schedule.weekday,
        day_of_month=schedule.day_of_month,
    )
    session.commit()
    return erp_sync.run_sync(session, trigger=SyncTrigger.AGENDADO)
