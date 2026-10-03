from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import SyncTrigger
from app.services import erp_schedule, erp_sync
from tests.erp_helpers import XLSX


def _ctx(client: TestClient) -> tuple[str, dict[str, str]]:
    round_id = client.get("/api/rounds").json()[0]["id"]
    users = {u["name"].split()[0]: u["id"] for u in client.get("/api/users").json()}
    return round_id, users


def _decide(client: TestClient, rec_id: str, user_id: str, decision: str, **kw) -> None:
    body = {"user_id": user_id, "decision": decision, **kw}
    assert client.post(f"/api/recommendations/{rec_id}/decisions", json=body).status_code == 201


# --- Produtos --------------------------------------------------------------------------------


def test_product_list(client: TestClient) -> None:
    page = client.get("/api/products").json()
    assert page["total"] == 40
    first = page["items"][0]
    assert first["sku"] == "PP-0001"
    assert [p["channel"] for p in first["prices"]] == ["LOJA_FISICA", "ECOMMERCE", "MARKETPLACE"]
    assert first["last_change"]["effective_date"] == "2026-09-01"
    assert first["price_changes"] == 2
    assert first["pending_recommendations"] == 3  # 3 canais pendentes na rodada atual

    assert client.get("/api/products", params={"abc_curve": "A"}).json()["total"] > 0
    assert client.get("/api/products", params={"q": "comedouro"}).json()["total"] >= 1
    assert client.get("/api/products", params={"status": "Descontinuando"}).json()["total"] == 2
    categories = client.get("/api/products/categories").json()
    assert "Rações" in categories
    by_cat = client.get("/api/products", params={"category": "Rações"}).json()
    assert all(p["category"] == "Rações" for p in by_cat["items"])


def test_product_detail_timeline(client: TestClient) -> None:
    round_id, users = _ctx(client)
    item = client.get(f"/api/rounds/{round_id}/recommendations", params={"q": "PP-0020"}).json()[
        "items"
    ][0]
    _decide(client, item["id"], users["Ana"], "APROVAR")

    detail = client.get("/api/products/PP-0020").json()
    assert detail["name"] == "Comedouro Inox M"
    assert len(detail["channels"]) == 3
    loja = next(c for c in detail["channels"] if c["channel"] == "LOJA_FISICA")
    assert loja["min_price_floor"] == round(loja["replacement_cost"] / (1 - loja["min_margin"]), 2)
    assert detail["stock"]["quantity"] > 0
    history = detail["price_history"]
    dates = [h["effective_date"] for h in history]
    assert dates == sorted(dates, reverse=True)
    assert {h["change_type"] for h in history} <= {"INICIAL", "AUMENTO", "REDUCAO"}
    assert len(detail["recommendations"]) == 3
    decided = next(r for r in detail["recommendations"] if r["id"] == item["id"])
    assert decided["status"] == "APROVADA"
    assert decided["last_decision"]["user_name"] == "Ana Souza"

    assert client.get("/api/products/PP-9999").status_code == 404


# --- Analistas -------------------------------------------------------------------------------


def test_analyst_history(client: TestClient) -> None:
    round_id, users = _ctx(client)
    subir = client.get(
        f"/api/rounds/{round_id}/recommendations",
        params={"recommendation": "SUBIR", "page_size": 4},
    ).json()["items"]
    _decide(client, subir[0]["id"], users["Ana"], "APROVAR")
    _decide(client, subir[1]["id"], users["Ana"], "REJEITAR", rejection_reason="Dados incorretos")
    _decide(client, subir[2]["id"], users["Ana"], "ADIAR")
    _decide(client, subir[3]["id"], users["Bruno"], "APROVAR")

    analysts = {a["name"]: a for a in client.get("/api/analysts").json()}
    ana = analysts["Ana Souza"]
    assert ana["decisions_total"] == 3
    assert ana["by_decision"] == {"APROVAR": 1, "EDITAR": 0, "REJEITAR": 1, "ADIAR": 1}
    assert ana["acceptance_base"] == 2 and ana["acceptance_rate"] == 0.5
    assert ana["rounds_count"] == 1 and ana["decisions_last_7_days"] == 3
    assert analysts["Carla Menezes"]["decisions_total"] == 0
    assert analysts["Carla Menezes"]["acceptance_rate"] is None

    detail = client.get(f"/api/analysts/{users['Ana']}").json()
    assert len(detail["decisions_by_day"]) == 30
    assert detail["decisions_by_day"][-1]["count"] == 3
    assert detail["by_recommendation"]["SUBIR"] == 3
    assert detail["rejection_reasons"] == {"Dados incorretos": 1}
    assert client.get("/api/analysts/00000000-0000-0000-0000-000000000000").status_code == 404


# --- Dashboard -------------------------------------------------------------------------------


def test_dashboard_with_round(client: TestClient) -> None:
    round_id, users = _ctx(client)
    items = client.get(f"/api/rounds/{round_id}/recommendations").json()["items"]
    _decide(client, items[0]["id"], users["Ana"], "APROVAR")
    _decide(client, items[1]["id"], users["Bruno"], "ADIAR")

    dash = client.get("/api/dashboard").json()
    r = dash["round"]
    assert r["round_date"] == "2026-09-09"
    assert (r["total"], r["decided"], r["pending"], r["postponed"], r["no_action"]) == (
        120, 1, 103, 1, 16,
    )  # fmt: skip
    assert r["high_risk_pending"] == 16
    assert dash["kpis"]["acceptance_rate"]["value"] == 1.0
    assert len(dash["top_pending"]) == 5
    assert all(t["status"] in ("PENDENTE", "ADIADA") for t in dash["top_pending"])
    assert dash["erp"]["products"] == 40
    assert dash["erp"]["last_sync"]["trigger"] == "INICIAL"
    assert len(dash["price_changes_by_month"]) == 6
    assert len(dash["decisions_by_day"]) == 14 and dash["decisions_by_day"][-1]["count"] == 2
    assert {a["name"]: a["decisions_round"] for a in dash["analysts"]}["Ana Souza"] == 1
    kinds = [a["kind"] for a in dash["recent_activity"]]
    assert "DECISAO" in kinds and "SYNC" in kinds
    assert dash["recent_activity"][0]["title"].startswith("Bruno Lima adiou")


def test_dashboard_without_round(api_client: TestClient, session: Session) -> None:
    erp_sync.run_sync(session, trigger=SyncTrigger.INICIAL, content=XLSX)
    erp_schedule.get_schedule(session)
    dash = api_client.get("/api/dashboard").json()
    assert dash["round"] is None and dash["kpis"] is None and dash["top_pending"] == []
    assert dash["erp"]["products"] == 40
    total_changes = sum(m["increases"] + m["decreases"] for m in dash["price_changes_by_month"])
    assert total_changes > 0
