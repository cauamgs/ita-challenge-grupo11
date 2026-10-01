from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(tags=["Saúde"])


@router.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.execute(text("select 1"))
        db_status = "ok"
    except Exception:
        db_status = "erro"
    return {"status": "ok", "db": db_status}
