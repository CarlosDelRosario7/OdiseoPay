"""Anulaciones con integridad, control de acceso y auditoría."""

from datetime import datetime

from src.extensions import db
from src.models import Anulacion, MovimientoInventario, Venta

from .conftest import auth
from .test_incremento3_nuevo import _crear_cliente, _crear_producto, _crear_proveedor


def crear_venta(client, token, producto, cliente, cantidad=2):
    response = client.post("/api/ventas", headers=auth(token), json={
        "id_cliente": cliente.id_cliente,
        "detalles": [{"id_producto": producto.id_producto, "cantidad": cantidad, "precio": "10.00"}],
    })
    assert response.status_code == 201
    return response.get_json()["id_venta"]


def crear_compra(client, token, producto, proveedor, cantidad=5):
    response = client.post("/api/compras", headers=auth(token), json={
        "id_proveedor": proveedor.id_proveedor,
        "detalles": [{"id_producto": producto.id_producto, "cantidad": cantidad, "precio": "5.00"}],
    })
    assert response.status_code == 201
    return response.get_json()["id_compra"]


def test_anular_venta_restaura_stock_y_guarda_evidencia(client, admin_token, admin_user):
    producto = _crear_producto("VentaAnulada", cantidad=10)
    cliente = _crear_cliente()
    venta_id = crear_venta(client, admin_token, producto, cliente)
    response = client.post(
        f"/api/ventas/{venta_id}/anulacion", headers=auth(admin_token),
        json={"motivo": "  Venta duplicada  "},
    )
    assert response.status_code == 200
    result = response.get_json()
    assert result["motivo"] == "Venta duplicada"
    assert result["usuario"] == admin_user.usuario
    assert result["id_usuario"] == admin_user.id_usuario
    assert datetime.fromisoformat(result["fecha_utc"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0
    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 10
    assert db.session.get(Venta, venta_id) is not None
    movimiento = db.session.scalar(db.select(MovimientoInventario).where(
        MovimientoInventario.motivo == f"Anulación de venta #{venta_id}"
    ))
    assert (movimiento.tipo, movimiento.cantidad, movimiento.id_usuario) == ("ENTRADA", 2, admin_user.id_usuario)
    listed = client.get("/api/ventas", headers=auth(admin_token)).get_json()["items"][0]
    assert listed["estado"] == "ANULADA"
    assert listed["anulacion"]["motivo"] == "Venta duplicada"


def test_anulacion_repetida_no_modifica_el_stock(client, admin_token):
    producto = _crear_producto("Duplicada", cantidad=10)
    venta_id = crear_venta(client, admin_token, producto, _crear_cliente())
    path = f"/api/ventas/{venta_id}/anulacion"
    assert client.post(path, headers=auth(admin_token), json={"motivo": "Error"}).status_code == 200
    assert client.post(path, headers=auth(admin_token), json={"motivo": "Repetida"}).status_code == 409
    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 10
    assert db.session.scalar(db.select(db.func.count()).select_from(Anulacion)) == 1


def test_motivo_obligatorio_y_admin(client, admin_token, vendedor_token):
    producto = _crear_producto("PermisosAnular", cantidad=10)
    venta_id = crear_venta(client, vendedor_token, producto, _crear_cliente())
    path = f"/api/ventas/{venta_id}/anulacion"
    assert client.post(path, json={"motivo": "Error"}).status_code == 401
    assert client.post(path, headers=auth(vendedor_token), json={"motivo": "Error"}).status_code == 403
    assert client.post(path, headers=auth(admin_token), json={"motivo": "  "}).status_code == 422
    assert client.post(path, headers=auth(admin_token), json={"motivo": "x" * 256}).status_code == 422
    assert client.post(path, headers=auth(admin_token), json=[]).status_code == 422
    assert db.session.scalar(db.select(db.func.count()).select_from(Anulacion)) == 0
    assert producto.inventario.cantidad == 8


def test_anular_compra_resta_stock_y_conserva_historial(client, admin_token):
    producto = _crear_producto("CompraAnulada", cantidad=2)
    compra_id = crear_compra(client, admin_token, producto, _crear_proveedor())
    response = client.post(
        f"/api/compras/{compra_id}/anulacion", headers=auth(admin_token),
        json={"motivo": "Compra duplicada"},
    )
    assert response.status_code == 200
    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 2
    movimiento = db.session.scalar(db.select(MovimientoInventario).where(
        MovimientoInventario.motivo == f"Anulación de compra #{compra_id}"
    ))
    assert (movimiento.tipo, movimiento.cantidad) == ("SALIDA", 5)
    listed = client.get("/api/compras", headers=auth(admin_token)).get_json()["items"][0]
    assert listed["estado"] == "ANULADA"
    assert listed["anulacion"]["motivo"] == "Compra duplicada"


def test_anular_compra_sin_stock_suficiente_no_cambia_nada(client, admin_token):
    producto = _crear_producto("SinStock", cantidad=0)
    compra_id = crear_compra(client, admin_token, producto, _crear_proveedor(), cantidad=5)
    crear_venta(client, admin_token, producto, _crear_cliente(), cantidad=4)
    response = client.post(
        f"/api/compras/{compra_id}/anulacion", headers=auth(admin_token),
        json={"motivo": "Error de proveedor"},
    )
    assert response.status_code == 409
    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 1
    assert db.session.scalar(db.select(db.func.count()).select_from(Anulacion)) == 0


def test_anulacion_de_operacion_inexistente(client, admin_token):
    response = client.post("/api/ventas/9999/anulacion", headers=auth(admin_token), json={"motivo": "Error"})
    assert response.status_code == 404
