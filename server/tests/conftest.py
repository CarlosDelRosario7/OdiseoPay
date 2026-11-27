"""Configuracion compartida de las pruebas del incremento 2.

Usa SQLite en memoria para no tocar la base MySQL de desarrollo.
"""

import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from src import create_app  # noqa: E402
from src.config import Config  # noqa: E402
from src.extensions import db  # noqa: E402
from src.models import Usuario  # noqa: E402
from src.utils.auth_utils import hash_password  # noqa: E402


class TestConfig(Config):
    TESTING = True
    RATELIMIT_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-secret-key-for-tests-only-32chars"
    AUTH0_DOMAIN = "test-tenant.us.auth0.com"
    AUTH0_AUDIENCE = "https://api.odiseopay.test"
    GEMINI_API_KEY = ""


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_user(app):
    user = Usuario(
        nombre="Administrador",
        usuario="admin",
        contrasena=hash_password("admin1234"),
        rol="Admin",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def vendedor_user(app):
    user = Usuario(
        nombre="Vendedor",
        usuario="vendedor1",
        contrasena=hash_password("vendedor1234"),
        rol="Vendedor",
    )
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, usuario, contrasena):
    response = client.post(
        "/api/auth/login",
        json={"usuario": usuario, "contrasena": contrasena},
    )
    assert response.status_code == 200, response.get_json()
    return response.get_json()["access_token"]


@pytest.fixture()
def admin_token(client, admin_user):
    return _login(client, "admin", "admin1234")


@pytest.fixture()
def vendedor_token(client, vendedor_user):
    return _login(client, "vendedor1", "vendedor1234")


def auth(token):
    return {"Authorization": f"Bearer {token}"}
