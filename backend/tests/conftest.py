import os

# Os testes rodam num banco separado; precisa ser definido antes de importar a aplicação.
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://popularpet:popularpet@db:5432/popularpet_test"
)

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]
SEED_DIR = Path(settings.seed_dir)
ROUND_CSV = SEED_DIR / "recomendacoes_rodada_2026-09-09.csv"
# A rodada de exemplo (saída do motor) pode não estar presente — p.ex. no pacote para quem vai
# implementar o motor. Os testes que dependem dela são pulados nesse caso.
ROUND_CSV_MISSING = (
    f"sem {ROUND_CSV.name} em seed/: gere uma rodada com o motor (ver docs/HANDOFF_MOTOR.md)"
)
requires_round_csv = pytest.mark.skipif(not ROUND_CSV.exists(), reason=ROUND_CSV_MISSING)

TABLES = (
    "price_history, erp_sync_runs, erp_sync_schedule, decisions, recommendations, rounds, "
    "stock_snapshot, product_channel_state, products, users"
)


@pytest.fixture(scope="session", autouse=True)
def _schema() -> None:
    with engine.begin() as conn:
        conn.execute(text("drop schema public cascade; create schema public"))
        for enum_name in (
            "channel_t", "recommendation_t", "risk_t", "decision_t", "user_role_t",
            "sync_trigger_t", "sync_status_t", "sync_frequency_t", "price_change_t",
        ):  # fmt: skip
            conn.execute(text(f"drop type if exists {enum_name} cascade"))
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")


@pytest.fixture
def session() -> Iterator[Session]:
    with engine.begin() as conn:
        conn.execute(text(f"truncate {TABLES} cascade"))
    with SessionLocal() as s:
        yield s


@pytest.fixture
def seeded(session: Session) -> Session:
    from app.seed import seed_all

    if not ROUND_CSV.exists():
        pytest.skip(ROUND_CSV_MISSING)

    seed_all(session, SEED_DIR)
    return session


@pytest.fixture
def client(seeded: Session) -> TestClient:
    from app.main import app

    return TestClient(app)


@pytest.fixture
def api_client(session: Session) -> TestClient:
    """Cliente da API sobre o banco vazio (sem seed)."""
    from app.main import app

    return TestClient(app)
