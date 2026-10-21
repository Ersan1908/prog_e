"""Проверки CORS для прямого обращения React к API с другого origin."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'cors.db'}")) as connection:
        yield connection


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://localhost:5173"])
def test_frontend_origin_can_read_response(client, origin):
    response = client.get("/api/v1/movies", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "origin" in response.headers["vary"].lower()


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_preflight_allows_mutations_and_json(client, method):
    origin = "http://127.0.0.1:5173"
    response = client.options(
        "/api/v1/movies/1",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert method in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()


def test_unlisted_origin_does_not_get_cors_permission(client):
    response = client.options(
        "/api/v1/movies",
        headers={
            "Origin": "https://other.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_origins_can_be_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://films.example, https://preview.example")
    with TestClient(create_app(f"sqlite:///{tmp_path / 'custom.db'}")) as connection:
        response = connection.get("/health", headers={"Origin": "https://films.example"})
        assert response.headers["access-control-allow-origin"] == "https://films.example"
        denied = connection.get("/health", headers={"Origin": "http://localhost:5173"})
        assert "access-control-allow-origin" not in denied.headers
