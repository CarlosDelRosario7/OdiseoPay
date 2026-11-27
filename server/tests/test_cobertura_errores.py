"""Respuestas ante errores, autenticación y operaciones genéricas."""

import runpy
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError, OperationalError

import src
from src.config import validate_jwt_secret
from src.extensions import db
from src.models import Categoria
from src.services.base_service import delete_record
from src.utils.auth_utils import login_required
from src.utils.security_log import _request_fields

from .conftest import TestConfig, auth
from .test_incremento3_nuevo import _crear_cliente, _crear_producto


def test_clave_jwt_insegura_se_rechaza():
    with pytest.raises(RuntimeError, match="insegura"):
        validate_jwt_secret("secret")
    assert validate_jwt_secret("  " + "a" * 32 + "  ") == "a" * 32


def test_arranque_directo_configura_debug_sin_abrir_servidor(app, monkeypatch):
    actual_create_app = src.create_app
    launches = []
    monkeypatch.setattr(src, "create_app", lambda: actual_create_app(TestConfig))
    monkeypatch.setattr(Flask, "run", lambda instance, **kwargs: launches.append(kwargs))
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setenv("FLASK_DEBUG", "1")
    runpy.run_path(str(Path(src.__file__).parent / "main.py"), run_name="__main__")
    assert launches == [{"debug": True}]


def test_jwt_invalido_y_expirado_son_rechazados(client, app):
    assert client.get("/api/productos", headers=auth("token-invalido")).status_code == 401
    token = create_access_token(identity="1", expires_delta=timedelta(seconds=-1))
    response = client.get("/api/productos", headers=auth(token))
    assert response.status_code == 401
    assert "expiró" in response.get_json()["error"]


def test_manejador_500_no_expone_detalles(client, app):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/test-error-interno")
    def fallo_controlado():
        raise RuntimeError("información interna sensible")

    response = client.get("/test-error-interno")
    assert response.status_code == 500
    assert response.get_json() == {"error": "Error interno del servidor"}


def test_login_required_exige_token(app, client, admin_user):
    @app.get("/test-protegido")
    @login_required
    def protected():
        return {"ok": True}

    assert client.get("/test-protegido").status_code == 401
    token = create_access_token(identity=str(admin_user.id_usuario))
    assert client.get("/test-protegido", headers=auth(token)).get_json() == {"ok": True}


def test_bitacora_recoge_ip_y_user_agent(app):
    with app.test_request_context(
        "/prueba", headers={"X-Forwarded-For": "192.0.2.5, 192.0.2.6", "User-Agent": "Prueba E4"},
    ):
        fields = _request_fields()
        assert fields["forwarded_for"] == "192.0.2.5"
        assert fields["user_agent"] == "Prueba E4"
        assert fields["path"] == "/prueba"


def test_consulta_individual_y_campos_no_nulos(client, admin_token):
    cliente = _crear_cliente()
    response = client.get(f"/api/clientes/{cliente.id_cliente}", headers=auth(admin_token))
    assert response.status_code == 200
    assert response.get_json()["id_cliente"] == cliente.id_cliente
    producto = _crear_producto("CampoNulo", cantidad=2)
    response = client.patch(
        f"/api/productos/{producto.id_producto}", headers=auth(admin_token), json={"nombre": None},
    )
    assert response.status_code == 422
    db.session.refresh(producto)
    assert producto.nombre == "CampoNulo"


def test_eliminar_categoria_sin_relaciones_y_servicio_directo(client, admin_token):
    primera = Categoria(nombre="Sin relaciones")
    segunda = Categoria(nombre="Servicio directo")
    db.session.add_all([primera, segunda])
    db.session.commit()
    id_primera, id_segunda = primera.id_categoria, segunda.id_categoria
    assert client.delete(f"/api/categorias/{id_primera}", headers=auth(admin_token)).status_code == 204
    delete_record(segunda)
    assert db.session.get(Categoria, id_primera) is None
    assert db.session.get(Categoria, id_segunda) is None


def test_cambio_de_usuario_y_rol_con_put(client, admin_token, vendedor_user):
    response = client.put(
        f"/api/usuarios/{vendedor_user.id_usuario}", headers=auth(admin_token),
        json={"usuario": "usuario_nuevo", "rol": "Admin"},
    )
    assert response.status_code == 200
    assert response.get_json()["usuario"] == "usuario_nuevo"
    assert response.get_json()["rol"] == "Admin"


def test_umbral_en_body_y_resumen_invalido(client, admin_token):
    response = client.get("/api/reportes/bajo-stock", headers=auth(admin_token), json={"umbral": 2})
    assert response.status_code == 200
    assert response.get_json()["umbral"] == 2
    assert client.get("/api/reportes/bajo-stock/resumen?umbral=no", headers=auth(admin_token)).status_code == 422


def integrity_error():
    return IntegrityError("SQL", {}, Exception("detalle interno"))


def operational_error(code):
    return OperationalError("SQL", {}, Exception(code, "detalle interno"))


@pytest.mark.parametrize("tipo", ["ventas", "compras"])
@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (integrity_error(), 409),
        (operational_error(1205), 409),
        (operational_error(9999), 500),
    ],
)
def test_venta_compra_manejan_errores_de_base_de_datos(client, app, admin_token, monkeypatch, tipo, error, expected):
    app.config["PROPAGATE_EXCEPTIONS"] = False
    path = "src.services.venta_service.create_sale" if tipo == "ventas" else "src.services.compra_service.create_purchase"

    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(path, fail)
    response = client.post(f"/api/{tipo}", headers=auth(admin_token), json={})
    assert response.status_code == expected
    assert "detalle interno" not in response.get_json()["error"]


@pytest.mark.parametrize(
    ("error", "expected"),
    [(integrity_error(), 409), (operational_error(1205), 409), (operational_error(9999), 500)],
)
def test_anulacion_maneja_conflictos_de_base_de_datos(client, app, admin_token, monkeypatch, error, expected):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr("src.routes.anulacion_routes.anular", fail)
    response = client.post("/api/ventas/1/anulacion", headers=auth(admin_token), json={"motivo": "Prueba"})
    assert response.status_code == expected
    assert "detalle interno" not in response.get_json()["error"]
