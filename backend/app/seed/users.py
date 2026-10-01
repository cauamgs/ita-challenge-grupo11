from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.repositories import users as users_repo

SEED_USERS = [
    ("Ana Souza", UserRole.ANALISTA),
    ("Bruno Lima", UserRole.ANALISTA),
    ("Carla Menezes", UserRole.GESTOR),
]


def seed_users(session: Session) -> int:
    created = 0
    for name, role in SEED_USERS:
        if users_repo.get_by_name(session, name) is None:
            session.add(User(name=name, role=role))
            created += 1
    session.flush()
    return created
