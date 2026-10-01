from fastapi import APIRouter

from app.api import decisions, health, metrics, recommendations, rounds, users

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(rounds.router)
api_router.include_router(recommendations.router)
api_router.include_router(decisions.router)
api_router.include_router(metrics.router)
