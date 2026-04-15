"""
Tests para la API de DataGob-IA
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["sistema"] == "DataGob-IA"
    assert data["acceso"] == "restringido"


def test_health():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_valido():
    response = client.post("/auth/token", data={
        "username": "analista01",
        "password": "Demo2024!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "analista"


def test_login_invalido():
    response = client.post("/auth/token", data={
        "username": "hacker",
        "password": "wrong"
    })
    assert response.status_code == 401


def test_population_stats_sin_auth():
    """Sin token debe rechazar."""
    response = client.get("/v1/poblacion/stats")
    assert response.status_code == 401


def test_population_stats_con_auth():
    """Con token válido debe retornar estadísticas."""
    login = client.post("/auth/token", data={
        "username": "analista01", "password": "Demo2024!"
    })
    token = login.json()["access_token"]

    response = client.get(
        "/v1/poblacion/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_registros" in data
    assert data["total_registros"] > 0


def test_fraude_alertas_rol_insuficiente():
    """Analista no puede acceder a alertas (requiere supervisor+)."""
    login = client.post("/auth/token", data={
        "username": "analista01", "password": "Demo2024!"
    })
    token = login.json()["access_token"]

    response = client.get(
        "/v1/fraude/alertas",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_fraude_alertas_supervisor():
    """Supervisor puede acceder a alertas."""
    login = client.post("/auth/token", data={
        "username": "supervisor01", "password": "Supervisor2024!"
    })
    token = login.json()["access_token"]

    response = client.get(
        "/v1/fraude/alertas",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    alertas = response.json()
    assert isinstance(alertas, list)
    assert len(alertas) > 0
    assert "severidad" in alertas[0]
