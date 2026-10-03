from fastapi import APIRouter

from app.api import (
    analysts,
    dashboard,
    decisions,
    erp,
    health,
    metrics,
    products,
    recommendations,
    rounds,
    users,
)

api_router = APIRouter(prefix="/api")
for module in (
    health, users, dashboard, rounds, recommendations, decisions, metrics, products, analysts, erp,
):  # fmt: skip
    api_router.include_router(module.router)
