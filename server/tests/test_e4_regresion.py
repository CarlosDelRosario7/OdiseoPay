"""Regresiones de integridad para el cierre del entregable 4."""

from src.extensions import db
from src.models import MovimientoInventario, Venta
from src.utils.auth_utils import verify_password

from .conftest import auth
from .test_incremento3_nuevo import _crear_cliente, _crear_producto


def test_precio_de_venta_manipulado_se_rechaza(client, admin_token):
    producto = _crear_producto("Precio", cantidad=10)
    cliente = _crear_cliente()
    response = client.post("/api/ventas", headers=auth(admin_token), json={
        "id_cliente": cliente.id_cliente,
        "detalles": [{"id_producto": producto.id_producto, "cantidad": 1, "precio": "0.01"}],
    })
    assert response.status_code == 422
    assert db.session.scalar(db.select(db.func.count()).select_from(Venta)) == 0
    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 10


def test_cliente_inexistente_se_rechaza(client, admin_token):
    producto = _crear_producto("Cliente", cantidad=10)
    response = client.post("/api/ventas", headers=auth(admin_token), json={
        "id_cliente": 9999,
        "detalles": [{"id_producto": producto.id_producto, "cantidad": 1, "precio": "10.00"}],
    })
    assert response.status_code == 422
    assert db.session.scalar(db.select(db.func.count()).select_from(Venta)) == 0


def test_venta_con_detalle_invalido_revierte_todos_los_cambios(client, admin_token):
    producto = _crear_producto("Rollback", cantidad=10)
    cliente = _crear_cliente()
    response = client.post("/api/ventas", headers=auth(admin_token), json={
        "id_cliente": cliente.id_cliente,
        "detalles": [
            {"id_producto": producto.id_producto, "cantidad": 2, "precio": "10.00"},
            {"id_producto": producto.id_producto, "cantidad": 100, "precio": "10.00"},
        ],
    })
    assert response.status_code == 422
    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 10
    assert db.session.scalar(db.select(db.func.count()).select_from(Venta)) == 0
    assert db.session.scalar(db.select(db.func.count()).select_from(MovimientoInventario)) == 0


def test_venta_usa_precio_de_catalogo_si_no_se_envia(client, vendedor_token):
    producto = _crear_producto("Catalogo", cantidad=10)
    cliente = _crear_cliente()
    response = client.post("/api/ventas", headers=auth(vendedor_token), json={
        "id_cliente": cliente.id_cliente,
        "detalles": [{"id_producto": producto.id_producto, "cantidad": 2}],
    })
    assert response.status_code == 201
    venta = db.session.get(Venta, response.get_json()["id_venta"])
    assert str(venta.detalles[0].precio) == "10.00"
    assert producto.inventario.cantidad == 8


def test_vendedor_puede_consultar_clientes(client, vendedor_token):
    _crear_cliente()
    response = client.get("/api/clientes", headers=auth(vendedor_token))
    assert response.status_code == 200
    assert response.get_json()["total"] == 1


def test_ajuste_inventario_registra_usuario_y_delta(client, admin_token, admin_user):
    producto = _crear_producto("Ajuste", cantidad=10)
    response = client.patch(
        f"/api/inventario/{producto.inventario.id_inventario}",
        headers=auth(admin_token), json={"cantidad": 7},
    )
    assert response.status_code == 200
    movimiento = db.session.scalar(db.select(MovimientoInventario))
    assert (movimiento.tipo, movimiento.cantidad, movimiento.id_usuario) == (
        "AJUSTE", -3, admin_user.id_usuario,
    )
    assert producto.inventario.cantidad == 7


def test_ajuste_negativo_no_modifica_inventario(client, admin_token):
    producto = _crear_producto("Invalido", cantidad=10)
    response = client.patch(
        f"/api/inventario/{producto.inventario.id_inventario}",
        headers=auth(admin_token), json={"cantidad": -1},
    )
    assert response.status_code == 422
    assert producto.inventario.cantidad == 10
    assert db.session.scalar(db.select(db.func.count()).select_from(MovimientoInventario)) == 0


def test_vendedor_no_puede_ajustar_inventario(client, vendedor_token):
    producto = _crear_producto("Permiso", cantidad=10)
    response = client.patch(
        f"/api/inventario/{producto.inventario.id_inventario}",
        headers=auth(vendedor_token), json={"cantidad": 5},
    )
    assert response.status_code == 403
    assert producto.inventario.cantidad == 10


def test_operaciones_comerciales_no_se_pueden_mutar_directamente(client, admin_token):
    headers = auth(admin_token)
    for path in ("/api/ventas/1", "/api/compras/1", "/api/detalle-ventas/1", "/api/detalle-compras/1"):
        assert client.patch(path, headers=headers, json={}).status_code == 405
        assert client.delete(path, headers=headers).status_code == 405
    for path in ("/api/detalle-ventas", "/api/detalle-compras"):
        assert client.post(path, headers=headers, json={}).status_code == 405


def test_rol_desconocido_no_puede_guardarse(client, admin_token, admin_user):
    response = client.patch(
        f"/api/usuarios/{admin_user.id_usuario}",
        headers=auth(admin_token), json={"rol": "SuperRoot"},
    )
    assert response.status_code == 422
    assert admin_user.rol == "Admin"


def test_actualizacion_con_grafia_original_hashea_contrasena(client, admin_token, admin_user):
    response = client.patch(
        f"/api/usuarios/{admin_user.id_usuario}",
        headers=auth(admin_token), json={"contraseña": "clave-nueva"},
    )
    assert response.status_code == 200
    db.session.refresh(admin_user)
    assert admin_user.contrasena != "clave-nueva"
    assert verify_password(admin_user.contrasena, "clave-nueva")


def test_registro_inicial_sin_campos_obligatorios_devuelve_422(client):
    response = client.post("/api/auth/registro", json={"rol": "Admin"})
    assert response.status_code == 422
