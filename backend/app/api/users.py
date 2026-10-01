from fastapi import APIRouter

from app.api.deps import SessionDep
from app.repositories import users as users_repo
from app.schemas.users import UserOut

router = APIRouter(tags=["Usuários"])


@router.get("/users", response_model=list[UserOut], summary="Lista usuários ativos")
def list_users(session: SessionDep) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in users_repo.list_active(session)]
