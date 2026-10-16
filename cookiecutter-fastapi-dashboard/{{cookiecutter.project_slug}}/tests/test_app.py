"""Tests de fumée : démarrage de l'app, probes, OpenAPI et protection JWT (sans PostgreSQL ni Redis)."""
from fastapi.testclient import TestClient

from app.main import app

# Pas de `with TestClient(...)` : le lifespan (connexion Redis) n'est pas déclenché.
client = TestClient(app)


def test_liveness():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_openapi_lists_only_get_routes():
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "{{ cookiecutter.project_name }}"
    assert "/api/v1/dashboards/kpis/exemple" in schema["paths"]
    for operations in schema["paths"].values():
        assert set(operations) <= {"get"}


def test_kpi_requires_token():
    response = client.get("/api/v1/dashboards/kpis/exemple")
    assert response.status_code in (401, 403)


def test_security_headers_and_request_id():
    response = client.get("/healthz", headers={"X-Request-ID": "abc"})
    assert response.headers["X-Request-ID"] == "abc"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
