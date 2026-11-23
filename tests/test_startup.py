from fastapi.testclient import TestClient

from app.main import app


def test_staff_panel_and_assets_are_served():
    with TestClient(app) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Katalog książek" in page.text
        for asset in ("/static/style.css", "/static/panel.js"):
            assert asset in page.text
            assert client.get(asset).status_code == 200


def test_app_starts_with_postgres_and_serves_openapi():
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Library management API"
