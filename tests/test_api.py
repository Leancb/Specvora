from fastapi.testclient import TestClient

from specvora.main import app


def test_home_exposes_human_authority() -> None:
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.json()["authority"] == "human"
