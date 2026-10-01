from fastapi.testclient import TestClient


def test_health(api_client: TestClient) -> None:
    response = api_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}
