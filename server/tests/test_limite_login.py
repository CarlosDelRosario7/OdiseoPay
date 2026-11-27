"""Límite de intentos fallidos de autenticación local."""

import pytest

from src import create_app
from src.extensions import db, limiter
from src.models import Usuario
from src.utils.auth_utils import hash_password

from .conftest import TestConfig


@pytest.fixture()
def limited_client():
    class LimitedConfig(TestConfig):
        RATELIMIT_ENABLED = True

    app = create_app(LimitedConfig)
    with app.app_context():
        limiter.reset()
        db.create_all()
        db.session.add(Usuario(nombre="Admin", usuario="admin", contrasena=hash_password("correcta"), rol="Admin"))
        db.session.commit()
        yield app.test_client()
        limiter.reset()
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def test_cinco_fallos_bloquean_sexto_intento(limited_client):
    for _ in range(5):
        assert limited_client.post("/api/auth/login", json={"usuario": "admin", "contrasena": "mal"}).status_code == 401
    response = limited_client.post("/api/auth/login", json={"usuario": "admin", "contrasena": "correcta"})
    assert response.status_code == 429
    assert "intentos" in response.get_json()["error"].lower()


def test_accesos_correctos_no_consumen_cuota(limited_client):
    for _ in range(6):
        assert limited_client.post("/api/auth/login", json={"usuario": "admin", "contrasena": "correcta"}).status_code == 200
    for _ in range(5):
        assert limited_client.post("/api/auth/login", json={"usuario": "admin", "contrasena": "mal"}).status_code == 401
    assert limited_client.post("/api/auth/login", json={"usuario": "admin", "contrasena": "correcta"}).status_code == 429


def test_limite_es_independiente_por_direccion_ip(limited_client):
    for _ in range(5):
        assert limited_client.post(
            "/api/auth/login", json={"usuario": "admin", "contrasena": "mal"},
            environ_base={"REMOTE_ADDR": "192.0.2.1"},
        ).status_code == 401
    assert limited_client.post(
        "/api/auth/login", json={"usuario": "admin", "contrasena": "correcta"},
        environ_base={"REMOTE_ADDR": "192.0.2.2"},
    ).status_code == 200
