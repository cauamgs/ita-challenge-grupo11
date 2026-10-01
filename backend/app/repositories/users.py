import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def list_active(session: Session) -> list[User]:
    return list(session.scalars(select(User).where(User.active).order_by(User.name)))


def get(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def get_by_name(session: Session, name: str) -> User | None:
    return session.scalar(select(User).where(User.name == name))
