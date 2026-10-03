"""Leitura do estado da integração com o ERP (status, execuções, agenda)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ErpSyncRun,
    ErpSyncSchedule,
    PriceChangeType,
    PriceHistory,
    Product,
    ProductChannelState,
    SyncStatus,
)
from app.schemas.common import Page
from app.schemas.erp import ErpStatus, ScheduleOut, SyncRunOut
from app.services import erp_schedule, erp_sync


def run_out(run: ErpSyncRun) -> SyncRunOut:
    duration = (run.finished_at - run.started_at).total_seconds() if run.finished_at else None
    return SyncRunOut(
        id=run.id,
        trigger=run.trigger.value,
        source=run.source,
        status=run.status.value,
        user_name=run.user.name if run.user else None,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_seconds=round(duration, 2) if duration is not None else None,
        reference_date=run.reference_date,
        products_total=run.products_total,
        products_new=run.products_new,
        products_updated=run.products_updated,
        prices_changed=run.prices_changed,
        history_imported=run.history_imported,
        stock_updated=run.stock_updated,
        message=run.message,
    )


def schedule_out(schedule: ErpSyncSchedule) -> ScheduleOut:
    return ScheduleOut(
        enabled=schedule.enabled,
        frequency=schedule.frequency,
        weekday=schedule.weekday,
        day_of_month=schedule.day_of_month,
        time_of_day=schedule.time_of_day.strftime("%H:%M"),
        description=erp_schedule.describe(
            schedule.frequency, schedule.time_of_day, schedule.weekday, schedule.day_of_month
        ),
        next_run_at=schedule.next_run_at,
        last_run_at=schedule.last_run_at,
        updated_by_name=schedule.user.name if schedule.user else None,
        updated_at=schedule.updated_at,
    )


def list_runs(session: Session, page: int, page_size: int) -> Page[SyncRunOut]:
    total = session.scalar(select(func.count()).select_from(ErpSyncRun)) or 0
    runs = session.scalars(
        select(ErpSyncRun)
        .order_by(ErpSyncRun.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return Page(items=[run_out(r) for r in runs], total=total, page=page, page_size=page_size)


def _last_run(session: Session, only_success: bool = False) -> ErpSyncRun | None:
    query = select(ErpSyncRun).order_by(ErpSyncRun.started_at.desc()).limit(1)
    if only_success:
        query = query.where(ErpSyncRun.status == SyncStatus.SUCESSO)
    return session.scalar(query)


def status(session: Session) -> ErpStatus:
    last, success = _last_run(session), _last_run(session, only_success=True)
    return ErpStatus(
        source=erp_sync.ERP_SOURCE_LABEL,
        source_file=erp_sync.default_source_file().name,
        last_sync=run_out(last) if last else None,
        last_success=run_out(success) if success else None,
        schedule=schedule_out(erp_schedule.get_schedule(session)),
        products=session.scalar(select(func.count()).select_from(Product)) or 0,
        channel_prices=session.scalar(
            select(
                func.count(
                    func.distinct(func.concat(ProductChannelState.sku, ProductChannelState.channel))
                )
            )
        )
        or 0,
        price_changes=session.scalar(
            select(func.count())
            .select_from(PriceHistory)
            .where(PriceHistory.change_type != PriceChangeType.INICIAL)
        )
        or 0,
        last_reference_date=session.scalar(select(func.max(ProductChannelState.reference_date))),
    )
