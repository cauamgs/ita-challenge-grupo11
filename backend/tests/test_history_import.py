import csv
import io
from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.conftest import ROUND_CSV, requires_round_csv

pytestmark = requires_round_csv


def _csv(new_date: str | None = None) -> bytes:
    text = ROUND_CSV.read_text(encoding="utf-8")
    if new_date:
        text = text.replace("2026-09-09", new_date)
    return text.encode("utf-8")


def _import(client: TestClient, content: bytes, **params):
    return client.post(
        "/api/rounds/import",
        params=params,
        files={"file": ("rodada.csv", content, "text/csv")},
    )


def test_import_same_csv_with_new_date_creates_second_round(client: TestClient) -> None:
    response = _import(client, _csv("2026-09-16"))
    assert response.status_code == 201, response.text
    assert response.json()["round_date"] == "2026-09-16"
    assert response.json()["imported"] == 120
    rounds = client.get("/api/rounds").json()
    assert [r["round_date"] for r in rounds] == ["2026-09-16", "2026-09-09"]  # mais recente 1º
    assert rounds[0]["source"] == "csv_import"
    summary = client.get(f"/api/rounds/{rounds[0]['id']}/summary").json()
    assert summary["by_recommendation"] == {"SUBIR": 20, "BAIXAR": 38, "MANTER": 16, "REVISAR": 46}


def test_import_existing_date_conflicts_unless_replace(client: TestClient) -> None:
    conflict = _import(client, _csv())
    assert conflict.status_code == 409
    assert "Já existe uma rodada em 09/09/2026" in conflict.json()["detail"]
    assert _import(client, _csv(), replace="true").status_code == 201
    assert len(client.get("/api/rounds").json()) == 1


def test_replace_blocked_when_round_has_decisions(client: TestClient) -> None:
    round_id = client.get("/api/rounds").json()[0]["id"]
    user_id = client.get("/api/users").json()[0]["id"]
    item = client.get(f"/api/rounds/{round_id}/recommendations").json()["items"][0]
    client.post(
        f"/api/recommendations/{item['id']}/decisions",
        json={"user_id": user_id, "decision": "APROVAR"},
    )
    response = _import(client, _csv(), replace="true")
    assert response.status_code == 409
    assert "já tem decisões" in response.json()["detail"]


def test_import_invalid_csv_returns_row_errors(client: TestClient) -> None:
    bad = _csv("2026-09-20").decode().replace(",BAIXAR,215.79,", ",DESCER,215.79,", 1)
    response = _import(client, bad.encode())
    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "CSV inválido."
    assert body["errors"][0]["linha"] == 2
    assert body["errors"][0]["campo"] == "recomendacao"
    assert _import(client, b"").status_code == 422


def test_history_lists_all_rounds_newest_first(client: TestClient) -> None:
    users = client.get("/api/users").json()
    ana, bruno = users[0]["id"], users[1]["id"]
    _import(client, _csv("2026-09-16"))
    rounds = client.get("/api/rounds").json()
    first = client.get(f"/api/rounds/{rounds[1]['id']}/recommendations").json()["items"][0]
    second = client.get(f"/api/rounds/{rounds[0]['id']}/recommendations").json()["items"][0]
    post = "/api/recommendations/{}/decisions"
    client.post(post.format(first["id"]), json={"user_id": ana, "decision": "APROVAR"})
    client.post(
        post.format(second["id"]),
        json={"user_id": bruno, "decision": "REJEITAR", "rejection_reason": "Outro"},
    )

    history = client.get("/api/decisions").json()
    assert history["total"] == 2
    latest = history["items"][0]
    assert latest["user_name"] == "Bruno Lima"
    assert latest["round_date"] == "2026-09-16"
    assert latest["sku"] == "PP-0020"
    assert latest["product_name"] == "Comedouro Inox M"
    assert history["items"][1]["round_date"] == "2026-09-09"

    # decisões do mesmo SKU × canal aparecem no histórico do item nas duas rodadas
    detail = client.get(f"/api/recommendations/{second['id']}").json()
    assert [d["round_date"] for d in detail["decision_history"]] == ["2026-09-16", "2026-09-09"]


def test_history_filters_and_export(client: TestClient) -> None:
    round_id = client.get("/api/rounds").json()[0]["id"]
    users = client.get("/api/users").json()
    items = client.get(f"/api/rounds/{round_id}/recommendations").json()["items"]
    post = "/api/recommendations/{}/decisions"
    client.post(post.format(items[0]["id"]), json={"user_id": users[0]["id"], "decision": "ADIAR"})
    client.post(
        post.format(items[1]["id"]), json={"user_id": users[1]["id"], "decision": "APROVAR"}
    )

    assert client.get("/api/decisions", params={"user_id": users[1]["id"]}).json()["total"] == 1
    assert client.get("/api/decisions", params={"decision": "ADIAR"}).json()["total"] == 1
    channel = items[1]["channel"]
    by_channel = client.get("/api/decisions", params={"channel": channel}).json()
    assert all(i["channel"] == channel for i in by_channel["items"])
    today = date.today()
    assert (
        client.get("/api/decisions", params={"date_from": str(today - timedelta(days=1))}).json()[
            "total"
        ]
        == 2
    )
    tomorrow = str(today + timedelta(days=2))
    assert client.get("/api/decisions", params={"date_from": tomorrow}).json()["total"] == 0

    response = client.get("/api/decisions/export", params={"decision": "APROVAR"})
    assert response.status_code == 200
    assert 'filename="historico_decisoes_' in response.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert len(rows) == 1
    assert rows[0]["analista"] == "Bruno Lima"
    assert rows[0]["decisao"] == "APROVAR"
    assert rows[0]["rodada"] == "2026-09-09"
