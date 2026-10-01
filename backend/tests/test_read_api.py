from fastapi.testclient import TestClient


def _round_id(client: TestClient) -> str:
    return client.get("/api/rounds").json()[0]["id"]


def _list(client: TestClient, **params) -> dict:
    response = client.get(f"/api/rounds/{_round_id(client)}/recommendations", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_users(client: TestClient) -> None:
    names = [u["name"] for u in client.get("/api/users").json()]
    assert names == ["Ana Souza", "Bruno Lima", "Carla Menezes"]


def test_rounds_list(client: TestClient) -> None:
    rounds = client.get("/api/rounds").json()
    assert len(rounds) == 1
    assert rounds[0]["round_date"] == "2026-09-09"
    assert rounds[0]["counts"] == {
        "total": 120, "SUBIR": 20, "BAIXAR": 38, "MANTER": 16, "REVISAR": 46,
    }  # fmt: skip


def test_summary(client: TestClient) -> None:
    summary = client.get(f"/api/rounds/{_round_id(client)}/summary").json()
    assert summary["total"] == 120
    assert summary["with_change"] == 58
    assert summary["by_recommendation"] == {"SUBIR": 20, "BAIXAR": 38, "MANTER": 16, "REVISAR": 46}
    assert summary["review_reasons"]["campanha"] == 18
    assert summary["review_reasons"]["cobertura_curta"] == 20
    assert summary["review_reasons"]["dados_frageis"] == 6
    assert summary["requires_approval"] == 52
    assert summary["top_value_at_stake"]["sku"] == "PP-0020"
    assert summary["top_value_at_stake"]["channel"] == "LOJA_FISICA"
    assert summary["decided"] == 0
    assert summary["pending"] == 104  # MANTER sem decisão não conta como pendente
    assert summary["summary_text"].startswith(
        "120 itens · 58 com sugestão de alteração · 46 exigem"
    )
    assert summary["summary_text"].endswith("Maior valor em jogo: PP-0020 na Loja física.")


def test_list_default_order_and_pagination(client: TestClient) -> None:
    page = _list(client)
    assert page["total"] == 120
    assert page["page_size"] == 25
    assert [i["priority"] for i in page["items"]] == list(range(1, 26))
    page5 = _list(client, page=5)
    assert [i["priority"] for i in page5["items"]] == list(range(101, 121))


def test_list_filters(client: TestClient) -> None:
    assert _list(client, recommendation="BAIXAR")["total"] == 38
    assert _list(client, channel="MARKETPLACE")["total"] == 40
    assert _list(client, requires_approval=True)["total"] == 52
    assert _list(client, status="PENDENTE")["total"] == 104
    assert _list(client, status="DECIDIDO")["total"] == 0
    curve_a = _list(client, abc_curve="A", page_size=200)["items"]
    assert curve_a and all(i["abc_curve"] == "A" for i in curve_a)
    high = _list(client, risk_level="ALTO", page_size=200)
    assert high["total"] == 16
    combined = _list(client, recommendation="REVISAR", channel="LOJA_FISICA", risk_level="ALTO")
    assert all(
        i["recommendation"] == "REVISAR" and i["channel"] == "LOJA_FISICA"
        for i in combined["items"]
    )


def test_list_search(client: TestClient) -> None:
    by_sku = _list(client, q="pp-0020")
    assert by_sku["total"] == 3
    by_name = _list(client, q="comedouro")
    assert by_name["total"] >= 3
    assert all("Comedouro" in i["product_name"] for i in by_name["items"])


def test_list_sort_value_at_stake(client: TestClient) -> None:
    items = _list(client, sort="value_at_stake", order="desc", page_size=200)["items"]
    values = [i["value_at_stake"] for i in items]
    with_value = [v for v in values if v is not None]
    assert with_value == sorted(with_value, reverse=True)
    assert values[-16:] == [None] * 16  # MANTER no fim, sem valor em jogo
    manter = [i for i in items if i["recommendation"] == "MANTER"]
    assert all(i["value_at_stake"] is None and i["status"] == "SEM_ACAO" for i in manter)


def test_list_sort_risk(client: TestClient) -> None:
    items = _list(client, sort="risk", order="desc", page_size=200)["items"]
    rank = {"BAIXO": 0, "MEDIO": 1, "ALTO": 2}
    ranks = [rank[i["risk_level"]] for i in items]
    assert ranks == sorted(ranks, reverse=True)


def test_list_invalid_filter(client: TestClient) -> None:
    response = client.get(
        f"/api/rounds/{_round_id(client)}/recommendations", params={"channel": "LOJA"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Parâmetros inválidos."


def test_unknown_round(client: TestClient) -> None:
    response = client.get("/api/rounds/00000000-0000-0000-0000-000000000000/summary")
    assert response.status_code == 404
    assert response.json() == {"detail": "Rodada não encontrada."}


def test_detail(client: TestClient) -> None:
    first = _list(client, page_size=1)["items"][0]
    detail = client.get(f"/api/recommendations/{first['id']}").json()
    assert detail["sku"] == "PP-0020"
    assert detail["product"]["name"] == "Comedouro Inox M"
    assert detail["justification"].startswith("preço +2.3% vs. mediana")
    assert detail["value_at_stake"] == 2010.97
    # piso = custo / (1 − margem mínima) = 139.05 / 0.70
    assert detail["min_price_floor"] == 198.64
    assert detail["decision_history"] == []
    assert detail["status"] == "PENDENTE"


def test_framework_errors_in_portuguese(client: TestClient) -> None:
    assert client.get("/api/nada").json() == {"detail": "Recurso não encontrado."}
    assert client.delete("/api/rounds").json() == {"detail": "Método não permitido."}
