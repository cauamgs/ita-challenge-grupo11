from fastapi.testclient import TestClient


def _ctx(client: TestClient) -> tuple[str, str]:
    return client.get("/api/rounds").json()[0]["id"], client.get("/api/users").json()[0]["id"]


def _metrics(client: TestClient, round_id: str, **params) -> dict:
    response = client.get(f"/api/rounds/{round_id}/metrics", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_metrics_without_decisions(client: TestClient) -> None:
    round_id, _ = _ctx(client)
    m = _metrics(client, round_id)
    assert m["items"] == 120
    assert m["acceptance_rate"]["value"] is None
    assert m["acceptance_rate"]["note"] == "nenhuma decisão registrada"
    assert m["acceptance_rate"]["target"] == 0.7
    assert m["estimated_review_hours"]["value"] == 0
    assert m["reversal_rate"] == {
        "value": None, "target": 0.03, "numerator": None, "denominator": None,
        "note": "não disponível na v1",
    }  # fmt: skip
    assert m["recommendation_distribution"] == {
        "SUBIR": 20, "BAIXAR": 38, "MANTER": 16, "REVISAR": 46,
    }  # fmt: skip
    assert 0 < m["in_competitive_band"]["value"] <= 1
    assert 0.2 < m["avg_gross_margin"]["value"] < 0.5
    assert set(m["price_index_by_curve"]) == {"A", "B", "C"}
    assert m["decisions_by_recommendation"]["MANTER"]["SEM_ACAO"] == 16
    assert m["decisions_by_recommendation"]["BAIXAR"]["PENDENTE"] == 38
    assert sum(m["rejection_reasons"].values()) == 0
    assert len(m["top_value_at_stake"]) == 10
    assert m["top_value_at_stake"][0]["sku"] == "PP-0011"


def test_metrics_reflect_decisions(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    subir = client.get(
        f"/api/rounds/{round_id}/recommendations",
        params={"recommendation": "SUBIR", "page_size": 3},
    ).json()["items"]
    url = "/api/recommendations/{}/decisions"
    client.post(url.format(subir[0]["id"]), json={"user_id": user_id, "decision": "APROVAR"})
    client.post(url.format(subir[1]["id"]), json={"user_id": user_id, "decision": "APROVAR"})
    client.post(
        url.format(subir[2]["id"]),
        json={"user_id": user_id, "decision": "REJEITAR", "rejection_reason": "Dados incorretos"},
    )
    m = _metrics(client, round_id)
    assert m["acceptance_rate"]["numerator"] == 2
    assert m["acceptance_rate"]["denominator"] == 3
    assert round(m["acceptance_rate"]["value"], 4) == 0.6667
    assert m["estimated_review_hours"]["value"] == 0.1  # 3 × 2 min
    assert m["decisions_by_recommendation"]["SUBIR"]["APROVADA"] == 2
    assert m["decisions_by_recommendation"]["SUBIR"]["REJEITADA"] == 1
    assert m["decisions_by_recommendation"]["SUBIR"]["PENDENTE"] == 17
    assert m["rejection_reasons"]["Dados incorretos"] == 1


def test_metrics_filters(client: TestClient) -> None:
    round_id, _ = _ctx(client)
    m = _metrics(client, round_id, channel="MARKETPLACE", abc_curve="A")
    assert m["filters"] == {"channel": "MARKETPLACE", "abc_curve": "A"}
    assert 0 < m["items"] < 40
    assert all(t["channel"] == "MARKETPLACE" for t in m["top_value_at_stake"])
    assert m["price_index_by_curve"]["B"] is None
