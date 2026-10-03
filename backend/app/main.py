import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api import api_router
from app.api.errors import register_error_handlers
from app.config import settings
from app.scheduler import scheduler_loop


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(scheduler_loop()) if settings.scheduler_enabled else None
    yield
    if task is not None:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="Popular Pet · Precificação Inteligente",
    description="API do protótipo: recomendações de preço, decisões do analista, métricas, "
    "integração simulada com o ERP e histórico de preços.",
    version="0.2.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
register_error_handlers(app)
app.include_router(api_router)
