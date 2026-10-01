import uuid

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.recommendations import RecommendationDetail
from app.services import recommendations as recs_service

router = APIRouter(tags=["Recomendações"])


@router.get(
    "/recommendations/{rec_id}",
    response_model=RecommendationDetail,
    summary="Detalhe da recomendação com histórico de decisões do SKU × canal",
)
def get_recommendation(rec_id: uuid.UUID, session: SessionDep) -> RecommendationDetail:
    return recs_service.get_detail(session, rec_id)
