from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.engine import CsvImportEngine, CsvValidationError
from app.services import rounds as rounds_service
from app.services.errors import ConflictError, ValidationFailed
from tests.conftest import ROUND_CSV, requires_round_csv

pytestmark = requires_round_csv


def _csv(transform=lambda s: s) -> bytes:
    return transform(ROUND_CSV.read_text(encoding="utf-8")).encode("utf-8")


def test_engine_parses_seed_csv() -> None:
    engine = CsvImportEngine(_csv())
    assert engine.detect_round_date() == date(2026, 9, 9)
    items = engine.run(date(2026, 9, 9))
    assert len(items) == 120
    assert items[0].sku == "PP-0020" and items[0].priority == 1


def test_engine_reports_row_errors() -> None:
    content = _csv(lambda s: s.replace(",BAIXAR,215.79,", ",DESCER,215.79,", 1))
    with pytest.raises(CsvValidationError) as exc:
        CsvImportEngine(content).run(date(2026, 9, 9))
    assert exc.value.errors[0]["linha"] == 2
    assert exc.value.errors[0]["campo"] == "recomendacao"


def test_engine_reports_missing_columns() -> None:
    content = _csv(lambda s: s.replace("justificativa,", "texto,", 1))
    with pytest.raises(CsvValidationError) as exc:
        CsvImportEngine(content).detect_round_date()
    assert exc.value.errors == [{"linha": 1, "campo": "justificativa", "erro": "coluna ausente"}]


def test_import_same_date_conflicts(seeded: Session) -> None:
    with pytest.raises(ConflictError):
        rounds_service.import_csv(seeded, _csv())


def test_import_new_date_creates_round(seeded: Session) -> None:
    new_round = rounds_service.import_csv(
        seeded, _csv(lambda s: s.replace("2026-09-09", "2026-09-10"))
    )
    assert new_round.round_date == date(2026, 9, 10)
    assert len(new_round.recommendations) == 120


def test_import_replace_without_decisions(seeded: Session) -> None:
    replaced = rounds_service.import_csv(seeded, _csv(), replace=True)
    assert len(replaced.recommendations) == 120


def test_import_unknown_sku_fails(seeded: Session) -> None:
    content = _csv(lambda s: s.replace("2026-09-09", "2026-09-11").replace("PP-0020", "PP-9999"))
    with pytest.raises(ValidationFailed) as exc:
        rounds_service.import_csv(seeded, content)
    assert "PP-9999" in exc.value.errors[0]["erro"]
