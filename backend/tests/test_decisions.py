import csv
import io

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Recommendation
from app.repositories import recommendations as recs_repo
from app.services.metrics import acceptance


def _ctx(client: TestClient) -> tuple[str, str]:
    round_id = client.get("/api/rounds").json()[0]["id"]
    user_id = client.get("/api/users").json()[0]["id"]
    return round_id, user_id


def _item(client: TestClient, round_id: str, **params) -> dict:
    params.setdefault("page_size", 1)
    return client.get(f"/api/rounds/{round_id}/recommendations", params=params).json()["items"][0]


def _decide(client: TestClient, rec_id: str, **body):
    return client.post(f"/api/recommendations/{rec_id}/decisions", json=body)


def test_approve_uses_suggested_price(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    item = _item(client, round_id)
    response = _decide(client, item["id"], user_id=user_id, decision="APROVAR", applied_price=1)
    assert response.status_code == 201
    body = response.json()
    assert body["decision"]["applied_price"] == item["suggested_price"]
    assert body["decision"]["user_name"] == "Ana Souza"
    assert body["decision"]["snapshot_recommendation"] == "BAIXAR"
    assert body["warnings"] == []
    updated = _item(client, round_id)
    assert updated["status"] == "APROVADA"
    assert updated["last_decision"]["decision"] == "APROVAR"


def test_edit_requires_positive_price(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    item = _item(client, round_id)
    missing = _decide(client, item["id"], user_id=user_id, decision="EDITAR")
    assert missing.status_code == 422
    assert missing.json()["detail"] == "Informe o novo preço para editar."
    zero = _decide(client, item["id"], user_id=user_id, decision="EDITAR", applied_price=0)
    assert zero.status_code == 422


def test_edit_warnings_do_not_block(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    item = _item(client, round_id)  # PP-0020 Loja física: atual 220,71; piso 198,64
    ok = _decide(client, item["id"], user_id=user_id, decision="EDITAR", applied_price=214.9)
    assert ok.status_code == 201
    assert ok.json()["warnings"] == []
    low = _decide(client, item["id"], user_id=user_id, decision="EDITAR", applied_price=190)
    assert low.status_code == 201
    assert low.json()["warnings"] == [
        "Preço abaixo do piso de margem mínima (R$ 198,64) (R01)",
        "Variação acima de 5% em relação ao preço atual (R02)",
    ]
    assert low.json()["decision"]["applied_price"] == 190.0


def test_reject_requires_reason(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    item = _item(client, round_id)
    missing = _decide(client, item["id"], user_id=user_id, decision="REJEITAR")
    assert missing.status_code == 422
    assert missing.json()["detail"] == "Informe o motivo da rejeição."
    invalid = _decide(
        client, item["id"], user_id=user_id, decision="REJEITAR", rejection_reason="x"
    )
    assert invalid.status_code == 422
    ok = _decide(
        client,
        item["id"],
        user_id=user_id,
        decision="REJEITAR",
        rejection_reason="Estratégia comercial",
        comment="  campanha regional  ",
    )
    assert ok.status_code == 201
    assert ok.json()["decision"]["applied_price"] is None
    assert ok.json()["decision"]["comment"] == "campanha regional"


def test_postpone_keeps_item_pending(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    item = _item(client, round_id)
    assert _decide(client, item["id"], user_id=user_id, decision="ADIAR").status_code == 201
    updated = _item(client, round_id)
    assert updated["status"] == "ADIADA"
    pending_ids = {
        i["id"]
        for i in client.get(
            f"/api/rounds/{round_id}/recommendations",
            params={"status": "PENDENTE", "page_size": 200},
        ).json()["items"]
    }
    assert item["id"] in pending_ids


def test_redo_appends_new_record(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    item = _item(client, round_id)
    _decide(client, item["id"], user_id=user_id, decision="APROVAR")
    _decide(client, item["id"], user_id=user_id, decision="REJEITAR", rejection_reason="Outro")
    detail = client.get(f"/api/recommendations/{item['id']}").json()
    assert detail["status"] == "REJEITADA"
    assert [d["decision"] for d in detail["decision_history"]] == ["REJEITAR", "APROVAR"]
    summary = client.get(f"/api/rounds/{round_id}/summary").json()
    assert summary["decided"] == 1
    assert summary["pending"] == 103


def test_unknown_user_or_recommendation(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    item = _item(client, round_id)
    fake = "00000000-0000-0000-0000-000000000000"
    assert _decide(client, item["id"], user_id=fake, decision="ADIAR").status_code == 404
    assert _decide(client, fake, user_id=user_id, decision="ADIAR").status_code == 404


def test_acceptance_rate(client: TestClient, seeded: Session) -> None:
    round_id, user_id = _ctx(client)
    subir = client.get(
        f"/api/rounds/{round_id}/recommendations",
        params={"recommendation": "SUBIR", "page_size": 5},
    ).json()["items"]
    manter = _item(client, round_id, recommendation="MANTER")
    a, b, c, d, e = subir
    _decide(client, a["id"], user_id=user_id, decision="APROVAR")
    # edição dentro de 1% do preço atual: aceite
    near = round(b["suggested_price"] + 0.009 * b["current_price"], 2)
    _decide(client, b["id"], user_id=user_id, decision="EDITAR", applied_price=near)
    # edição longe do sugerido: não é aceite
    _decide(client, c["id"], user_id=user_id, decision="EDITAR", applied_price=c["current_price"])
    _decide(client, d["id"], user_id=user_id, decision="REJEITAR", rejection_reason="Outro")
    _decide(client, e["id"], user_id=user_id, decision="ADIAR")  # fora do denominador
    _decide(client, manter["id"], user_id=user_id, decision="APROVAR")  # MANTER não entra

    round_uuid = seeded.scalar(select(Recommendation.round_id).limit(1))
    seeded.expire_all()
    result = acceptance(recs_repo.all_for_round(seeded, round_uuid))
    assert (result.numerator, result.denominator) == (2, 4)
    assert result.value == 0.5


def test_export_current_approved_and_edited(client: TestClient) -> None:
    round_id, user_id = _ctx(client)
    items = client.get(f"/api/rounds/{round_id}/recommendations", params={"page_size": 4}).json()[
        "items"
    ]
    _decide(
        client, items[0]["id"], user_id=user_id, decision="APROVAR", comment="ok, sem ressalvas"
    )
    _decide(client, items[1]["id"], user_id=user_id, decision="EDITAR", applied_price=200)
    _decide(client, items[2]["id"], user_id=user_id, decision="REJEITAR", rejection_reason="Outro")
    _decide(client, items[3]["id"], user_id=user_id, decision="APROVAR")
    _decide(client, items[3]["id"], user_id=user_id, decision="ADIAR")  # vigente = ADIAR

    response = client.get(f"/api/rounds/{round_id}/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    disposition = response.headers["content-disposition"]
    assert 'filename="decisoes_2026-09-09_' in disposition and disposition.endswith('.csv"')
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert [r["sku"] for r in rows] == [items[0]["sku"], items[1]["sku"]]
    assert list(rows[0]) == [
        "sku", "produto", "canal", "preco_atual", "preco_aplicado", "variacao", "decisao",
        "analista", "data_hora", "comentario",
    ]  # fmt: skip
    assert rows[0]["decisao"] == "APROVAR"
    assert rows[0]["preco_aplicado"] == f"{items[0]['suggested_price']:.2f}"
    assert rows[0]["canal"] == "Loja física"
    assert rows[0]["analista"] == "Ana Souza"
    assert rows[0]["comentario"] == "ok, sem ressalvas"
    assert rows[1]["decisao"] == "EDITAR"
    assert rows[1]["preco_aplicado"] == "200.00"
