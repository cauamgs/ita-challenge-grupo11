import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.models import (
    Decision,
    DecisionType,
    Product,
    ProductChannelState,
    Recommendation,
    Round,
    StockSnapshot,
    User,
)
from app.seed import seed_all
from tests.conftest import SEED_DIR


def _count(session: Session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model))


def test_seed_base_without_round(session: Session) -> None:
    """Usuários e base da empresa (xlsx) são carregados mesmo sem arquivo de rodada."""
    seed_all(session, SEED_DIR)
    seed_all(session, SEED_DIR)  # idempotente
    assert _count(session, User) == 3
    assert _count(session, Product) == 40
    assert _count(session, ProductChannelState) == 120
    assert _count(session, StockSnapshot) == 40


def test_seed_counts(seeded: Session) -> None:
    assert _count(seeded, User) == 3
    assert _count(seeded, Product) == 40
    assert _count(seeded, ProductChannelState) == 120
    assert _count(seeded, StockSnapshot) == 40
    assert _count(seeded, Round) == 1
    assert _count(seeded, Recommendation) == 120
    by_type = dict(
        seeded.execute(
            select(Recommendation.recommendation, func.count()).group_by(
                Recommendation.recommendation
            )
        ).all()
    )
    assert by_type == {"BAIXAR": 38, "SUBIR": 20, "MANTER": 16, "REVISAR": 46}


def test_seed_is_idempotent(seeded: Session) -> None:
    seed_all(seeded, SEED_DIR)
    assert _count(seeded, User) == 3
    assert _count(seeded, Product) == 40
    assert _count(seeded, ProductChannelState) == 120
    assert _count(seeded, StockSnapshot) == 40
    assert _count(seeded, Recommendation) == 120


def test_seed_maps_csv_fields(seeded: Session) -> None:
    rec = seeded.scalar(select(Recommendation).where(Recommendation.priority == 2))
    assert rec.sku == "PP-0019"
    assert rec.channel == "LOJA_FISICA"
    assert rec.risk_level == "MEDIO"
    assert rec.requires_approval is True
    assert rec.review_reasons == [
        "sinais conflitantes: redução com cobertura de 1 dias e sem reposição (R11)"
    ]
    assert rec.data_alerts == []
    assert rec.product.name == "Caixa Transporte M"


def test_decisions_are_append_only(seeded: Session) -> None:
    rec = seeded.scalar(select(Recommendation).limit(1))
    user = seeded.scalar(select(User).limit(1))
    decision = Decision(
        recommendation_id=rec.id,
        user_id=user.id,
        decision=DecisionType.ADIAR,
        snapshot_recommendation=rec.recommendation,
        snapshot_suggested_price=rec.suggested_price,
        snapshot_current_price=rec.current_price,
    )
    seeded.add(decision)
    seeded.commit()
    with pytest.raises(DBAPIError, match="append-only"):
        seeded.execute(text("update decisions set comment = 'x'"))
    seeded.rollback()
    with pytest.raises(DBAPIError, match="append-only"):
        seeded.execute(text("delete from decisions"))
    seeded.rollback()
