from fastapi.testclient import TestClient

from app.main import app


def test_app_starts_with_postgres_and_serves_openapi():
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Library management API"
