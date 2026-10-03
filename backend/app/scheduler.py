"""Laço em segundo plano que dispara a sincronização automática com o ERP quando chega a hora."""

import asyncio
import logging

from app.config import settings
from app.db import SessionLocal
from app.services.erp_schedule import run_due_sync

log = logging.getLogger(__name__)


def _tick() -> None:
    with SessionLocal() as session:
        run = run_due_sync(session)
        if run is not None:
            log.warning("Sincronização agendada com o ERP: %s — %s", run.status, run.message)


async def scheduler_loop() -> None:
    while True:
        await asyncio.sleep(settings.scheduler_interval_seconds)
        try:
            await asyncio.to_thread(_tick)
        except Exception:  # nunca derruba a API por causa do agendador
            log.exception("Erro no agendador de sincronização")
