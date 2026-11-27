"""Pruebas de integracion de los endpoints del incremento 2.

Recorren el stack completo: ruta -> servicio -> modelo -> base de datos.
"""

import pytest

from src.extensions import db
from src.models import Categoria, Inventario, Producto, Proveedor, Usuario
from src.utils.auth_utils import hash_password, verify_password

from .conftest import auth


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------

def test_health_responde_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


# --------------------------------------------------------------------------
# Login local
# --------------------------------------------------------------------------

def test_login_exitoso_devuelve_token_y_rol(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"usuario": "admin", "contrasena": "admin1234"},
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["access_token"]
    assert body["rol"] == "Admin"
    assert body["usuario"] == "admin"
    assert "contrasena" not in body
    assert "contraseña" not in body


def test_login_contrasena_incorrecta(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"usuario": "admin", "contrasena": "mala"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Credenciales inválidas"


def test_login_usuario_inexistente(client):
    response = client.post(
        "/api/auth/login",
        json={"usuario": "nadie", "contrasena": "x"},
    )
    assert response.status_code == 401


def test_login_sin_body(client):
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 401


# --------------------------------------------------------------------------
# Registro publico (FR-002)
# --------------------------------------------------------------------------

def test_registro_primer_usuario_admin(client):
    response = client.post(
        "/api/auth/registro",
        json={
            "nombre": "Primer Admin",
            "usuario": "primer",
            "contrasena": "clave1234",
            "rol": "Admin",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["id_usuario"]


def test_registro_primer_usuario_no_admin_rechazado(client):
    response = client.post(
        "/api/auth/registro",
        json={
            "nombre": "Primer Vendedor",
            "usuario": "primer",
            "contrasena": "clave1234",
            "rol": "Vendedor",
        },
    )
    assert response.status_code == 422
    assert "Admin" in response.get_json()["error"]


def test_registro_rol_invalido(client):
    response = client.post(
        "/api/auth/registro",
        json={
            "nombre": "X",
            "usuario": "x",
            "contrasena": "clave1234",
            "rol": "SuperAdmin",
        },
    )
    assert response.status_code == 422


def test_registro_bloqueado_si_ya_hay_usuarios(client, admin_user):
    response = client.post(
        "/api/auth/registro",
        json={
            "nombre": "Otro",
            "usuario": "otro",
            "contrasena": "clave1234",
            "rol": "Admin",
        },
    )
    assert response.status_code == 401


# --------------------------------------------------------------------------
# Auth0
# --------------------------------------------------------------------------

def test_auth0_login_sin_token(client):
    response = client.post("/api/auth/auth0/login")
    assert response.status_code == 401


def test_auth0_login_token_invalido(client):
    response = client.post(
        "/api/auth/auth0/login",
        headers={"Authorization": "Bearer token-falso"},
    )
    assert response.status_code == 401


def test_auth0_login_no_configurado(client, app):
    app.config["AUTH0_DOMAIN"] = ""
    response = client.post(
        "/api/auth/auth0/login",
        headers={"Authorization": "Bearer token-falso"},
    )
    assert response.status_code == 503


def test_vincular_auth0_sin_token_local(client):
    response = client.post("/api/auth/auth0/vincular", json={"auth0_token": "x"})
    assert response.status_code == 401


def test_vincular_auth0_sin_auth0_token(client, admin_token):
    response = client.post(
        "/api/auth/auth0/vincular",
        json={},
        headers=auth(admin_token),
    )
    assert response.status_code == 422


def test_desvincular_auth0_sin_vinculo(client, admin_token):
    response = client.delete("/api/auth/auth0/vincular", headers=auth(admin_token))
    assert response.status_code == 200
    assert "no tiene una cuenta social" in response.get_json()["message"]


def test_desvincular_auth0_con_vinculo(client, admin_token, admin_user):
    admin_user.auth0_sub = "google-oauth2|123"
    db.session.commit()

    response = client.delete("/api/auth/auth0/vincular", headers=auth(admin_token))

    assert response.status_code == 204
    db.session.refresh(admin_user)
    assert admin_user.auth0_sub is None


# --------------------------------------------------------------------------
# Usuarios (FR-004 a FR-008)
# --------------------------------------------------------------------------

def test_listar_usuarios_requiere_token(client):
    assert client.get("/api/usuarios").status_code == 401


def test_listar_usuarios_como_admin(client, admin_token, admin_user):
    response = client.get("/api/usuarios", headers=auth(admin_token))
    body = response.get_json()

    assert response.status_code == 200
    assert body["total"] == 1
    assert "contrasena" not in body["items"][0]
    assert "contraseña" not in body["items"][0]


def test_listar_usuarios_como_vendedor_prohibido(client, vendedor_token):
    response = client.get("/api/usuarios", headers=auth(vendedor_token))
    assert response.status_code == 403


def test_crear_usuario_como_admin(client, admin_token):
    response = client.post(
        "/api/usuarios",
        json={
            "nombre": "Nuevo Vendedor",
            "usuario": "nuevo",
            "contrasena": "clave1234",
            "rol": "Vendedor",
        },
        headers=auth(admin_token),
    )
    assert response.status_code == 201
    assert response.get_json()["id_usuario"]


def test_crear_usuario_duplicado(client, admin_token, admin_user):
    response = client.post(
        "/api/usuarios",
        json={
            "nombre": "Duplicado",
            "usuario": "admin",
            "contrasena": "clave1234",
            "rol": "Vendedor",
        },
        headers=auth(admin_token),
    )
    assert response.status_code == 409


def test_crear_usuario_campos_faltantes(client, admin_token):
    response = client.post(
        "/api/usuarios",
        json={"nombre": "Solo nombre"},
        headers=auth(admin_token),
    )
    assert response.status_code == 422


def test_actualizar_usuario_con_put(client, admin_token, admin_user):
    response = client.put(
        f"/api/usuarios/{admin_user.id_usuario}",
        json={"nombre": "Admin Renombrado"},
        headers=auth(admin_token),
    )
    assert response.status_code == 200
    assert response.get_json()["nombre"] == "Admin Renombrado"


def test_actualizar_contrasena_con_put(client, admin_token, admin_user):
    response = client.put(
        f"/api/usuarios/{admin_user.id_usuario}",
        json={"contrasena": "nuevaClave99"},
        headers=auth(admin_token),
    )
    assert response.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"usuario": "admin", "contrasena": "nuevaClave99"},
    )
    assert login.status_code == 200


def test_actualizar_usuario_con_patch(client, admin_token, admin_user):
    """El CRUD generico expone PATCH; el frontend lo usa para editar usuarios."""
    response = client.patch(
        f"/api/usuarios/{admin_user.id_usuario}",
        json={"nombre": "Via PATCH"},
        headers=auth(admin_token),
    )
    assert response.status_code == 200
    assert response.get_json()["nombre"] == "Via PATCH"


def test_actualizar_usuario_con_patch_cambia_contrasena(client, admin_token, admin_user):
    """El PATCH generico guarda la contrasena hasheada, no en texto plano."""
    response = client.patch(
        f"/api/usuarios/{admin_user.id_usuario}",
        json={"contrasena": "textoPlano99"},
        headers=auth(admin_token),
    )
    assert response.status_code == 200

    db.session.refresh(admin_user)
    assert admin_user.contrasena != "textoPlano99"
    assert verify_password(admin_user.contrasena, "textoPlano99") is True


def test_actualizar_usuario_nombre_duplicado(client, admin_token, admin_user, vendedor_user):
    response = client.put(
        f"/api/usuarios/{vendedor_user.id_usuario}",
        json={"usuario": "admin"},
        headers=auth(admin_token),
    )
    assert response.status_code == 409


# --------------------------------------------------------------------------
# Reporte de bajo stock
# --------------------------------------------------------------------------

def _crear_inventario(nombre, cantidad, stock_minimo):
    categoria = Categoria(nombre=f"Cat {nombre}", descripcion="")
    proveedor = Proveedor(nombre=f"Prov {nombre}", telefono="", correo="", direccion="")
    db.session.add_all([categoria, proveedor])
    db.session.flush()
    producto = Producto(
        nombre=nombre,
        descripcion="",
        precio_compra="5.00",
        precio_venta="12.50",
        id_categoria=categoria.id_categoria,
        id_proveedor=proveedor.id_proveedor,
    )
    db.session.add(producto)
    db.session.flush()
    db.session.add(
        Inventario(
            id_producto=producto.id_producto,
            cantidad=cantidad,
            stock_minimo=stock_minimo,
            ubicacion="Estante A1",
        )
    )
    db.session.commit()
    return producto


def test_bajo_stock_requiere_token(client):
    assert client.get("/api/reportes/bajo-stock").status_code == 401


def test_bajo_stock_lista_productos(client, admin_token):
    _crear_inventario("Bajo", cantidad=2, stock_minimo=5)
    _crear_inventario("Normal", cantidad=40, stock_minimo=5)

    response = client.get("/api/reportes/bajo-stock", headers=auth(admin_token))
    body = response.get_json()

    assert response.status_code == 200
    assert body["total"] == 1
    item = body["items"][0]
    assert item["nombre_producto"] == "Bajo"
    assert item["faltante"] == 3
    assert item["precio_venta"] == "12.50"
    assert body["umbral"] is None


def test_bajo_stock_con_umbral(client, admin_token):
    _crear_inventario("A", cantidad=3, stock_minimo=1)
    _crear_inventario("B", cantidad=20, stock_minimo=1)

    response = client.get(
        "/api/reportes/bajo-stock?umbral=5",
        headers=auth(admin_token),
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["umbral"] == 5
    assert body["total"] == 1


def test_bajo_stock_umbral_invalido(client, admin_token):
    response = client.get(
        "/api/reportes/bajo-stock?umbral=abc",
        headers=auth(admin_token),
    )
    assert response.status_code == 422


def test_bajo_stock_umbral_negativo(client, admin_token):
    response = client.get(
        "/api/reportes/bajo-stock?umbral=-1",
        headers=auth(admin_token),
    )
    assert response.status_code == 422


def test_bajo_stock_accesible_para_vendedor(client, vendedor_token):
    _crear_inventario("Bajo", cantidad=1, stock_minimo=5)

    response = client.get("/api/reportes/bajo-stock", headers=auth(vendedor_token))
    assert response.status_code == 200


def test_resumen_bajo_stock(client, admin_token):
    _crear_inventario("A", cantidad=1, stock_minimo=5)
    _crear_inventario("B", cantidad=2, stock_minimo=5)
    _crear_inventario("C", cantidad=50, stock_minimo=5)

    response = client.get(
        "/api/reportes/bajo-stock/resumen",
        headers=auth(admin_token),
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["total"] == 2
    assert body["umbral"] is None


def test_resumen_bajo_stock_con_umbral(client, admin_token):
    _crear_inventario("A", cantidad=1, stock_minimo=1)
    _crear_inventario("B", cantidad=9, stock_minimo=1)

    response = client.get(
        "/api/reportes/bajo-stock/resumen?umbral=5",
        headers=auth(admin_token),
    )
    assert response.get_json()["total"] == 1


def test_actualizar_stock_minimo_como_admin(client, admin_token):
    producto = _crear_inventario("A", cantidad=1, stock_minimo=5)

    response = client.patch(
        f"/api/reportes/bajo-stock/{producto.id_producto}",
        json={"stock_minimo": 15},
        headers=auth(admin_token),
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["stock_minimo"] == 15


def test_actualizar_stock_minimo_como_vendedor_prohibido(client, vendedor_token):
    producto = _crear_inventario("A", cantidad=1, stock_minimo=5)

    response = client.patch(
        f"/api/reportes/bajo-stock/{producto.id_producto}",
        json={"stock_minimo": 15},
        headers=auth(vendedor_token),
    )
    assert response.status_code == 403


def test_actualizar_stock_minimo_valor_invalido(client, admin_token):
    producto = _crear_inventario("A", cantidad=1, stock_minimo=5)

    response = client.patch(
        f"/api/reportes/bajo-stock/{producto.id_producto}",
        json={"stock_minimo": -3},
        headers=auth(admin_token),
    )
    assert response.status_code == 422


def test_actualizar_stock_minimo_producto_inexistente(client, admin_token):
    response = client.patch(
        "/api/reportes/bajo-stock/9999",
        json={"stock_minimo": 5},
        headers=auth(admin_token),
    )
    assert response.status_code == 404


# --------------------------------------------------------------------------
# Regresion: rutas existentes siguen funcionando
# --------------------------------------------------------------------------

def test_productos_requiere_token(client):
    assert client.get("/api/productos").status_code == 401


def test_productos_lista_vacia(client, admin_token):
    response = client.get("/api/productos", headers=auth(admin_token))
    body = response.get_json()

    assert response.status_code == 200
    assert body["items"] == []
    assert body["total"] == 0


def test_ruta_inexistente_devuelve_404(client):
    response = client.get("/api/no-existe")
    assert response.status_code == 404
