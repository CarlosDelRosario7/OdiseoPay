"""Autenticación federada probada sin contacto con servicios externos."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

from src.extensions import db
from src.utils.auth0_utils import validate_auth0_token

from .conftest import auth


def test_validacion_auth0_verifica_firma_audiencia_emisor_y_expiracion(app, monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    urls = []

    class JwksFake:
        def __init__(self, url):
            urls.append(url)

        def get_signing_key_from_jwt(self, token):
            assert token
            return SimpleNamespace(key=public_key)

    monkeypatch.setattr("src.utils.auth0_utils.PyJWKClient", JwksFake)
    claims = {
        "sub": "google-oauth2|prueba",
        "aud": app.config["AUTH0_AUDIENCE"],
        "iss": "https://test-tenant.us.auth0.com/",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")
    assert validate_auth0_token(token)["sub"] == claims["sub"]
    assert urls == ["https://test-tenant.us.auth0.com/.well-known/jwks.json"]
    bad = jwt.encode({**claims, "aud": "audiencia-incorrecta"}, private_key, algorithm="RS256")
    with pytest.raises(jwt.InvalidAudienceError):
        validate_auth0_token(bad)
    expired = jwt.encode({**claims, "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, private_key, algorithm="RS256")
    with pytest.raises(jwt.ExpiredSignatureError):
        validate_auth0_token(expired)


def test_validacion_auth0_requiere_configuracion(app):
    app.config["AUTH0_DOMAIN"] = ""
    with pytest.raises(RuntimeError, match="no está configurado"):
        validate_auth0_token("token")


def test_login_social_sin_sub_y_cuenta_no_vinculada(client, monkeypatch):
    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", lambda token: {})
    headers = {"Authorization": "Bearer token-de-prueba"}
    assert client.post("/api/auth/auth0/login", headers=headers).status_code == 401
    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", lambda token: {"sub": "google-oauth2|no-vinculada"})
    response = client.post("/api/auth/auth0/login", headers=headers)
    assert response.status_code == 403
    assert "vinculada" in response.get_json()["error"]


def test_login_social_vinculado_emite_jwt_local(client, admin_user, monkeypatch):
    admin_user.auth0_sub = "google-oauth2|cuenta"
    db.session.commit()
    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", lambda token: {"sub": "google-oauth2|cuenta"})
    response = client.post("/api/auth/auth0/login", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    result = response.get_json()
    assert result["access_token"]
    assert result["id_usuario"] == admin_user.id_usuario
    assert result["rol"] == "Admin"


@pytest.mark.parametrize(
    ("error", "status", "message"),
    [
        (RuntimeError("config"), 503, "no está configurado"),
        (jwt.ExpiredSignatureError("expirado"), 401, "expiró"),
        (jwt.InvalidTokenError("inválido"), 401, "inválido"),
        (ValueError("detalle interno"), 401, "No se pudo validar"),
    ],
)
def test_login_social_traduce_errores_sin_filtrar_detalles(client, monkeypatch, error, status, message):
    def reject(_token):
        raise error

    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", reject)
    response = client.post("/api/auth/auth0/login", headers={"Authorization": "Bearer token"})
    assert response.status_code == status
    assert message in response.get_json()["error"]
    assert "detalle interno" not in response.get_json()["error"]


def test_vinculacion_exige_configuracion_y_usuario_existente(client, app, admin_token):
    app.config["AUTH0_DOMAIN"] = ""
    assert client.post("/api/auth/auth0/vincular", headers=auth(admin_token), json={"auth0_token": "token"}).status_code == 503
    app.config["AUTH0_DOMAIN"] = "test-tenant.us.auth0.com"
    token = create_access_token(identity="99999", additional_claims={"rol": "Admin"})
    assert client.post("/api/auth/auth0/vincular", headers=auth(token), json={"auth0_token": "token"}).status_code == 404
    assert client.delete("/api/auth/auth0/vincular", headers=auth(token)).status_code == 404


def test_vincular_y_desvincular_cuenta_social(client, admin_user, admin_token, monkeypatch):
    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", lambda token: {"sub": "google-oauth2|nueva"})
    response = client.post("/api/auth/auth0/vincular", headers=auth(admin_token), json={"auth0_token": "token"})
    assert response.status_code == 200
    assert response.get_json()["auth0_provider"] == "Google"
    db.session.refresh(admin_user)
    assert admin_user.auth0_sub == "google-oauth2|nueva"
    repeat = client.post("/api/auth/auth0/vincular", headers=auth(admin_token), json={"auth0_token": "token"})
    assert repeat.status_code == 200
    assert "ya está vinculada" in repeat.get_json()["message"]
    assert client.delete("/api/auth/auth0/vincular", headers=auth(admin_token)).status_code == 204
    db.session.refresh(admin_user)
    assert admin_user.auth0_sub is None


def test_vinculacion_rechaza_sub_ausente_y_cuenta_distinta(client, admin_user, admin_token, monkeypatch):
    headers = auth(admin_token)
    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", lambda token: {})
    assert client.post("/api/auth/auth0/vincular", headers=headers, json={"auth0_token": "token"}).status_code == 401
    admin_user.auth0_sub = "google-oauth2|existente"
    db.session.commit()
    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", lambda token: {"sub": "facebook|otra"})
    response = client.post("/api/auth/auth0/vincular", headers=headers, json={"auth0_token": "token"})
    assert response.status_code == 409
    assert response.get_json()["auth0_sub"] == "google-oauth2|existente"


def test_vinculacion_rechaza_sub_de_otro_usuario(client, admin_token, vendedor_user, monkeypatch):
    vendedor_user.auth0_sub = "google-oauth2|ocupada"
    db.session.commit()
    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", lambda token: {"sub": "google-oauth2|ocupada"})
    response = client.post("/api/auth/auth0/vincular", headers=auth(admin_token), json={"auth0_token": "token"})
    assert response.status_code == 409
    assert "otro usuario" in response.get_json()["error"]


def test_vinculacion_revierte_conflicto_de_integridad(client, admin_user, admin_token, monkeypatch):
    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", lambda token: {"sub": "google-oauth2|conflicto"})
    with patch.object(db.session, "commit", side_effect=IntegrityError("insert", {}, Exception("conflicto"))):
        response = client.post("/api/auth/auth0/vincular", headers=auth(admin_token), json={"auth0_token": "token"})
    assert response.status_code == 409
    db.session.refresh(admin_user)
    assert admin_user.auth0_sub is None


def test_vinculacion_revierte_y_traduce_error_del_proveedor(client, admin_user, admin_token, monkeypatch):
    def reject(_token):
        raise jwt.ExpiredSignatureError("expirado")

    monkeypatch.setattr("src.routes.auth_routes.validate_auth0_token", reject)
    response = client.post("/api/auth/auth0/vincular", headers=auth(admin_token), json={"auth0_token": "token"})
    assert response.status_code == 401
    assert "expiró" in response.get_json()["error"]
    db.session.refresh(admin_user)
    assert admin_user.auth0_sub is None
