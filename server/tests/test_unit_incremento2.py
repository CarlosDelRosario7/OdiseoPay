"""Pruebas unitarias de la logica de negocio del incremento 2.

Cubren funciones puras y servicios, sin pasar por HTTP.
"""

import pytest

from src.extensions import db
from src.models import Categoria, Inventario, Producto, Proveedor, Usuario
from src.routes.auth_routes import _auth0_provider
from src.services import reporte_service, usuario_service
from src.utils.auth_utils import hash_password, verify_password
from src.utils.auth0_utils import is_auth0_configured


# --------------------------------------------------------------------------
# auth_utils: hash y verificacion de contrasenas
# --------------------------------------------------------------------------

def test_hash_password_no_guarda_texto_plano():
    hashed = hash_password("secreto123")
    assert hashed != "secreto123"
    assert len(hashed) > 20


def test_verify_password_acepta_correcta():
    hashed = hash_password("secreto123")
    assert verify_password(hashed, "secreto123") is True


def test_verify_password_rechaza_incorrecta():
    hashed = hash_password("secreto123")
    assert verify_password(hashed, "otra") is False


# --------------------------------------------------------------------------
# auth0_utils: deteccion de configuracion
# --------------------------------------------------------------------------

def test_is_auth0_configured_con_dominio_y_audiencia(app):
    assert is_auth0_configured() is True


def test_is_auth0_configured_sin_audiencia(app):
    app.config["AUTH0_AUDIENCE"] = ""
    assert is_auth0_configured() is False


def test_is_auth0_configured_sin_dominio(app):
    app.config["AUTH0_DOMAIN"] = ""
    assert is_auth0_configured() is False


# --------------------------------------------------------------------------
# auth_routes: traduccion del proveedor social
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "sub, esperado",
    [
        ("google-oauth2|123", "Google"),
        ("facebook|456", "Facebook"),
        ("auth0|789", "Auth0"),
        ("github|999", "github"),
        (None, None),
        ("", None),
    ],
)
def test_auth0_provider_traduce_sub(sub, esperado):
    assert _auth0_provider(sub) == esperado


# --------------------------------------------------------------------------
# usuario_service: creacion de usuarios
# --------------------------------------------------------------------------

def test_create_user_hashea_contrasena(app):
    user = usuario_service.create_user(
        {
            "nombre": "Nuevo",
            "usuario": "nuevo1",
            "contrasena": "clave1234",
            "rol": "Vendedor",
        }
    )
    assert user.id_usuario is not None
    assert user.contrasena != "clave1234"
    assert verify_password(user.contrasena, "clave1234") is True


def test_create_user_guarda_rol(app):
    user = usuario_service.create_user(
        {
            "nombre": "Admin Dos",
            "usuario": "admin2",
            "contrasena": "clave1234",
            "rol": "Admin",
        }
    )
    assert user.rol == "Admin"


# --------------------------------------------------------------------------
# reporte_service: bajo stock
# --------------------------------------------------------------------------

def _crear_producto(nombre, cantidad, stock_minimo, precio="10.00"):
    categoria = Categoria(nombre=f"Cat {nombre}", descripcion="")
    proveedor = Proveedor(nombre=f"Prov {nombre}", telefono="", correo="", direccion="")
    db.session.add_all([categoria, proveedor])
    db.session.flush()

    producto = Producto(
        nombre=nombre,
        descripcion="",
        precio_compra="5.00",
        precio_venta=precio,
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
            ubicacion="A1",
        )
    )
    db.session.commit()
    return producto


def test_bajo_stock_usa_stock_minimo_por_producto(app):
    _crear_producto("Bajo", cantidad=2, stock_minimo=5)
    _crear_producto("Normal", cantidad=50, stock_minimo=5)

    pagination = reporte_service.bajo_stock()

    assert pagination.total == 1
    assert pagination.items[0].producto.nombre == "Bajo"


def test_bajo_stock_con_umbral_global(app):
    _crear_producto("Uno", cantidad=3, stock_minimo=1)
    _crear_producto("Dos", cantidad=10, stock_minimo=1)

    pagination = reporte_service.bajo_stock(umbral=5)

    assert pagination.total == 1
    assert pagination.items[0].producto.nombre == "Uno"


def test_bajo_stock_umbral_cero_no_devuelve_nada(app):
    _crear_producto("Uno", cantidad=0, stock_minimo=5)

    pagination = reporte_service.bajo_stock(umbral=0)

    assert pagination.total == 0


def test_bajo_stock_ordena_por_cantidad_ascendente(app):
    _crear_producto("Tres", cantidad=3, stock_minimo=10)
    _crear_producto("Uno", cantidad=1, stock_minimo=10)

    pagination = reporte_service.bajo_stock()

    cantidades = [item.cantidad for item in pagination.items]
    assert cantidades == sorted(cantidades)


def test_resumen_bajo_stock_cuenta_productos(app):
    _crear_producto("A", cantidad=1, stock_minimo=5)
    _crear_producto("B", cantidad=2, stock_minimo=5)
    _crear_producto("C", cantidad=99, stock_minimo=5)

    assert reporte_service.resumen_bajo_stock() == 2


def test_resumen_bajo_stock_con_umbral(app):
    _crear_producto("A", cantidad=1, stock_minimo=1)
    _crear_producto("B", cantidad=2, stock_minimo=1)
    _crear_producto("C", cantidad=9, stock_minimo=1)

    assert reporte_service.resumen_bajo_stock(umbral=3) == 2


def test_actualizar_stock_minimo(app):
    producto = _crear_producto("A", cantidad=1, stock_minimo=5)

    inventario = reporte_service.actualizar_stock_minimo(producto.id_producto, 12)

    assert inventario is not None
    assert inventario.stock_minimo == 12


def test_actualizar_stock_minimo_producto_sin_inventario(app):
    categoria = Categoria(nombre="Cat", descripcion="")
    proveedor = Proveedor(nombre="Prov", telefono="", correo="", direccion="")
    db.session.add_all([categoria, proveedor])
    db.session.flush()
    producto = Producto(
        nombre="Sin inventario",
        descripcion="",
        precio_compra="1.00",
        precio_venta="2.00",
        id_categoria=categoria.id_categoria,
        id_proveedor=proveedor.id_proveedor,
    )
    db.session.add(producto)
    db.session.commit()

    assert reporte_service.actualizar_stock_minimo(producto.id_producto, 3) is None


# --------------------------------------------------------------------------
# Modelo Usuario: campo auth0_sub
# --------------------------------------------------------------------------

def test_usuario_auth0_sub_por_defecto_es_nulo(app):
    user = Usuario(
        nombre="Sin social",
        usuario="sinsocial",
        contrasena=hash_password("x1234"),
        rol="Vendedor",
    )
    db.session.add(user)
    db.session.commit()

    assert user.auth0_sub is None
