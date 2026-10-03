from datetime import datetime, time

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ErpSyncRun, PriceHistory, SyncFrequency, SyncTrigger
from app.services import erp_schedule, erp_sync
from tests.conftest import SEED_DIR
from tests.erp_helpers import XLSX, modified_workbook, without_sheet


def _initial(session: Session) -> None:
    erp_sync.run_sync(session, trigger=SyncTrigger.INICIAL, content=XLSX)


def _upload(client: TestClient, content: bytes, name: str = "erp.xlsx"):
    return client.post(
        "/api/erp/import",
        files={"file": (name, content, "application/vnd.ms-excel")},
    )


def test_initial_sync_loads_base_and_price_history(session: Session) -> None:
    _initial(session)
    run = session.scalar(select(ErpSyncRun))
    assert run.status == "SUCESSO"
    assert (run.products_total, run.products_new, run.prices_changed) == (40, 40, 0)
    assert run.history_imported == 120
    by_type = dict(
        session.execute(
            select(PriceHistory.change_type, func.count()).group_by(PriceHistory.change_type)
        ).all()
    )
    # 3 registros por SKU no histórico (1 inicial + 2 alterações) + preço inicial dos outros canais
    assert by_type["AUMENTO"] + by_type["REDUCAO"] == 80
    assert by_type["INICIAL"] == 40 + 80


def test_second_sync_without_changes(api_client: TestClient, session: Session) -> None:
    _initial(session)
    response = api_client.post("/api/erp/sync", json={})
    assert response.status_code == 201
    run = response.json()
    assert run["trigger"] == "MANUAL"
    assert run["status"] == "SUCESSO"
    assert (run["products_new"], run["products_updated"], run["prices_changed"]) == (0, 0, 0)
    assert run["history_imported"] == 0
    assert run["message"] == "40 produtos lidos · nenhum preço alterado"


def test_import_file_detects_price_and_catalog_changes(
    api_client: TestClient, session: Session
) -> None:
    _initial(session)
    content = modified_workbook(
        {
            "Precos_Atuais": [
                ({"SKU": "PP-0001", "Canal": "E-commerce"}, {"Preço atual": 4.49}),
                ({"SKU": "PP-0002", "Canal": "Marketplace"}, {"Preço atual": 13.90}),
            ],
            "Produtos": [({"SKU": "PP-0003"}, {"Status": "Descontinuando"})],
        }
    )
    response = _upload(api_client, content, "export_erp_2026-10-01.xlsx")
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["trigger"] == "ARQUIVO"
    assert run["source"] == "Arquivo · export_erp_2026-10-01.xlsx"
    assert (run["prices_changed"], run["products_updated"]) == (2, 1)

    detail = api_client.get("/api/products/PP-0001").json()
    latest = detail["price_history"][0]
    assert (latest["channel"], latest["change_type"]) == ("ECOMMERCE", "AUMENTO")
    assert (latest["old_price"], latest["new_price"]) == (4.29, 4.49)
    assert latest["variation"] == round(4.49 / 4.29 - 1, 4)
    ecommerce = next(c for c in detail["channels"] if c["channel"] == "ECOMMERCE")
    assert ecommerce["current_price"] == 4.49
    assert api_client.get("/api/products/PP-0003").json()["status"] == "Descontinuando"

    reduction = api_client.get("/api/products/PP-0002").json()["price_history"][0]
    assert reduction["change_type"] == "REDUCAO"


def test_invalid_files_are_logged_as_errors(api_client: TestClient, session: Session) -> None:
    _initial(session)
    broken = _upload(api_client, b"isto nao e uma planilha", "lixo.xlsx").json()
    assert broken["status"] == "ERRO"
    assert "não foi possível ler o arquivo" in broken["message"]

    missing = _upload(api_client, without_sheet("Estoque")).json()
    assert missing["status"] == "ERRO"
    assert "aba ausente: Estoque" in missing["message"]

    bad_channel = modified_workbook(
        {"Precos_Atuais": [({"SKU": "PP-0001", "Canal": "Marketplace"}, {"Canal": "Shopee"})]}
    )
    bad = _upload(api_client, bad_channel).json()
    assert bad["status"] == "ERRO"
    assert "canal inválido 'Shopee'" in bad["message"]

    # nada foi gravado pelas execuções com erro; todas aparecem no histórico
    assert session.scalar(select(func.count()).select_from(PriceHistory)) == 200
    syncs = api_client.get("/api/erp/syncs").json()
    assert syncs["total"] == 4
    assert [s["status"] for s in syncs["items"]] == ["ERRO", "ERRO", "ERRO", "SUCESSO"]
    status = api_client.get("/api/erp/status").json()
    assert status["last_sync"]["status"] == "ERRO"
    assert status["last_success"]["trigger"] == "INICIAL"


def test_empty_upload(api_client: TestClient) -> None:
    assert _upload(api_client, b"").status_code == 422


# --- Agenda ----------------------------------------------------------------------------------

SP_6AM = time(6, 0)


def _at(text: str) -> datetime:
    """Horário de São Paulo (UTC−3) escrito como texto local."""
    return datetime.fromisoformat(text + "-03:00")


def test_next_run_daily() -> None:
    before = erp_schedule.compute_next_run(SyncFrequency.DIARIA, SP_6AM, _at("2026-10-03T05:00"))
    after = erp_schedule.compute_next_run(SyncFrequency.DIARIA, SP_6AM, _at("2026-10-03T06:00"))
    assert before == _at("2026-10-03T06:00")
    assert after == _at("2026-10-04T06:00")


def test_next_run_weekly() -> None:
    # 03/10/2026 é sábado; segunda = 0
    monday = erp_schedule.compute_next_run(
        SyncFrequency.SEMANAL, SP_6AM, _at("2026-10-03T10:00"), weekday=0
    )
    assert monday == _at("2026-10-05T06:00")
    same_day_later = erp_schedule.compute_next_run(
        SyncFrequency.SEMANAL, SP_6AM, _at("2026-10-03T10:00"), weekday=5
    )
    assert same_day_later == _at("2026-10-10T06:00")


def test_next_run_monthly() -> None:
    assert erp_schedule.compute_next_run(
        SyncFrequency.MENSAL, SP_6AM, _at("2026-10-03T10:00"), day_of_month=10
    ) == _at("2026-10-10T06:00")
    assert erp_schedule.compute_next_run(
        SyncFrequency.MENSAL, SP_6AM, _at("2026-10-15T10:00"), day_of_month=15
    ) == _at("2026-11-15T06:00")
    assert erp_schedule.compute_next_run(
        SyncFrequency.MENSAL, SP_6AM, _at("2026-12-20T10:00"), day_of_month=1
    ) == _at("2027-01-01T06:00")


def test_describe_schedule() -> None:
    assert erp_schedule.describe(SyncFrequency.DIARIA, SP_6AM) == "Todos os dias às 06:00"
    assert erp_schedule.describe(SyncFrequency.SEMANAL, SP_6AM, 0) == "Toda segunda-feira às 06:00"
    assert erp_schedule.describe(SyncFrequency.SEMANAL, SP_6AM, 6) == "Todo domingo às 06:00"
    assert (
        erp_schedule.describe(SyncFrequency.MENSAL, time(23, 30), day_of_month=10)
        == "Todo dia 10 do mês às 23:30"
    )


def test_schedule_api(api_client: TestClient, session: Session) -> None:
    initial = api_client.get("/api/erp/schedule").json()
    assert initial["enabled"] is False and initial["next_run_at"] is None

    invalid = api_client.put(
        "/api/erp/schedule", json={"enabled": True, "frequency": "MENSAL", "time_of_day": "06:00"}
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"] == "Escolha um dia do mês entre 1 e 28."
    bad_time = api_client.put(
        "/api/erp/schedule", json={"enabled": True, "frequency": "DIARIA", "time_of_day": "25:00"}
    )
    assert bad_time.status_code == 422

    saved = api_client.put(
        "/api/erp/schedule",
        json={"enabled": True, "frequency": "MENSAL", "day_of_month": 15, "time_of_day": "07:30"},
    ).json()
    assert saved["description"] == "Todo dia 15 do mês às 07:30"
    assert saved["next_run_at"] is not None
    assert saved["weekday"] is None

    preview = api_client.post(
        "/api/erp/schedule/preview",
        json={"enabled": True, "frequency": "SEMANAL", "weekday": 2, "time_of_day": "06:00"},
    ).json()
    assert preview["description"] == "Toda quarta-feira às 06:00"

    off = api_client.put(
        "/api/erp/schedule", json={"enabled": False, "frequency": "DIARIA", "time_of_day": "06:00"}
    ).json()
    assert off["enabled"] is False and off["next_run_at"] is None


def test_scheduled_sync_runs_when_due(session: Session) -> None:
    _initial(session)
    now = _at("2026-10-03T10:00")
    erp_schedule.update_schedule(
        session,
        enabled=True,
        frequency=SyncFrequency.DIARIA,
        time_of_day=SP_6AM,
        weekday=None,
        day_of_month=None,
        user_id=None,
        now=now,
    )
    assert erp_schedule.run_due_sync(session, now) is None  # próxima é amanhã 06:00

    due = _at("2026-10-04T06:00:30")
    run = erp_schedule.run_due_sync(session, due)
    assert run is not None and run.trigger == SyncTrigger.AGENDADO and run.status == "SUCESSO"
    schedule = erp_schedule.get_schedule(session)
    assert schedule.last_run_at == due
    assert schedule.next_run_at == _at("2026-10-05T06:00")
    assert erp_schedule.run_due_sync(session, due) is None  # não roda duas vezes


def test_seed_creates_initial_sync_once(session: Session) -> None:
    from app.seed import seed_all

    seed_all(session, SEED_DIR)
    seed_all(session, SEED_DIR)
    assert session.scalar(select(func.count()).select_from(ErpSyncRun)) == 1
    assert erp_schedule.get_schedule(session).enabled is False
