from fastapi import FastAPI

from app.api import api_router
from app.api.errors import register_error_handlers

app = FastAPI(
    title="Popular Pet · Precificação Inteligente",
    description="API do protótipo v1: recomendações de preço, decisões do analista e métricas.",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)
register_error_handlers(app)
app.include_router(api_router)
