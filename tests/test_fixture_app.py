from fastapi.testclient import TestClient

from specvora.fixture_app import app


def test_controlled_fixture_target():
    client = TestClient(app)
    assert client.get("/pets/1").status_code == 200
    assert client.get("/pets/1", headers={"X-Specvora-Fixture": "rate-limit"}).status_code == 429
    assert (
        client.get("/pets/1", headers={"X-Specvora-Fixture": "dependency-failure"}).status_code
        == 503
    )
    assert client.get("/pets/1", headers={"X-Specvora-Fixture": "unknown"}).status_code == 400
    assert client.get("/pets/1", headers={"X-Specvora-Auth-Fixture": "valid"}).status_code == 200
    assert client.get("/pets/1", headers={"X-Specvora-Auth-Fixture": "expired"}).status_code == 401
    response = client.get(
        "/pets/1", headers={"X-Specvora-Auth-Fixture": "insufficient-scope"}
    )
    assert response.status_code == 403
    response = client.get("/pets/1", headers={"X-Specvora-Dependency-Fixture": "timeout"})
    assert response.status_code == 503
