"""Seed idempotente: pode rodar a cada `docker compose up` sem duplicar dados."""

from pathlib import Path

from sqlalchemy.orm import Session

from app.engine import CsvImportEngine
from app.repositories import rounds as rounds_repo
from app.seed.base_xlsx import seed_base
from app.seed.users import seed_users
from app.services import rounds as rounds_service

XLSX_FILE = "base_popular_pet.xlsx"
ROUND_CSV_GLOB = "recomendacoes_rodada_*.csv"


def seed_all(session: Session, seed_dir: Path) -> list[str]:
    log: list[str] = []
    created = seed_users(session)
    log.append(f"usuários criados: {created}")

    counts = seed_base(session, seed_dir / XLSX_FILE)
    log.append(f"base lida: {counts}")

    round_files = sorted(seed_dir.glob(ROUND_CSV_GLOB))
    if not round_files:
        log.append("nenhum arquivo de rodada em seed/: importe uma rodada pela tela ou pela API")
    for csv_path in round_files:
        engine = CsvImportEngine(csv_path.read_bytes(), csv_path.name)
        round_date = engine.detect_round_date()
        if rounds_repo.get_by_date(session, round_date) is not None:
            log.append(f"rodada {round_date} já existe: mantida")
            continue
        new_round = rounds_service.run_engine(
            session, engine, round_date, source_file=csv_path.name
        )
        log.append(f"rodada {round_date} importada: {len(new_round.recommendations)} itens")
    session.commit()
    return log
