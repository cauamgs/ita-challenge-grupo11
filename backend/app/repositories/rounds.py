import uuid
from datetime import date

from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app.models import Decision, Recommendation, Round


def get(session: Session, round_id: uuid.UUID) -> Round | None:
    return session.get(Round, round_id)


def get_by_date(session: Session, round_date: date) -> Round | None:
    return session.scalar(select(Round).where(Round.round_date == round_date))


def list_all(session: Session) -> list[Round]:
    return list(session.scalars(select(Round).order_by(Round.round_date.desc())))


def has_decisions(session: Session, round_id: uuid.UUID) -> bool:
    return bool(
        session.scalar(
            select(
                exists().where(
                    Decision.recommendation_id == Recommendation.id,
                    Recommendation.round_id == round_id,
                )
            )
        )
    )


def delete_round(session: Session, round_id: uuid.UUID) -> None:
    session.execute(delete(Round).where(Round.id == round_id))
