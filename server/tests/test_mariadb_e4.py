"""Pruebas opcionales en una base MariaDB exclusiva de E4.

Nunca crea ni elimina bases o tablas. Solo se activa con TEST_MARIADB_URI y
exige que el nombre de la base termine en ``_e4_test``.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url

from src import create_app
from src.extensions import db
from src.models import Categoria, Cliente, Inventario, Producto, Proveedor, Usuario
from src.utils.auth_utils import create_token, hash_password

from .conftest import TestConfig, auth


@pytest.fixture()
def mysql_data():
    uri = os.getenv("TEST_MARIADB_URI")
    if not uri:
        pytest.skip("TEST_MARIADB_URI no configurada")
    url = make_url(uri)
    if not url.drivername.startswith("mysql") or not (url.database or "").endswith("_e4_test"):
        pytest.fail("Se requiere una base exclusiva cuyo nombre termine en _e4_test")

    class MariaConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = uri

    app = create_app(MariaConfig)
    suffix = uuid4().hex[:12]
    with app.app_context():
        admin = Usuario(nombre="Prueba E4", usuario=f"e4_{suffix}", contrasena=hash_password("test-only"), rol="Admin")
        categoria = Categoria(nombre=f"E4 {suffix}")
        proveedor = Proveedor(nombre=f"E4 {suffix}")
        cliente = Cliente(nombre="Prueba", apellido="E4", correo=f"{suffix}@example.test")
        db.session.add_all([admin, categoria, proveedor, cliente])
        db.session.flush()
        producto = Producto(
            nombre=f"E4 {suffix}", precio_compra="5.00", precio_venta="10.00",
            id_categoria=categoria.id_categoria, id_proveedor=proveedor.id_proveedor,
        )
        db.session.add(producto)
        db.session.flush()
        db.session.add(Inventario(id_producto=producto.id_producto, cantidad=1, stock_minimo=1))
        db.session.commit()
        data = {
            "app": app, "token": create_token(admin), "producto": producto.id_producto,
            "cliente": cliente.id_cliente, "proveedor": proveedor.id_proveedor,
        }
        db.session.remove()
        yield data
        db.session.remove()
        db.engine.dispose()


def test_mariadb_ventas_y_anulaciones_concurrentes(mysql_data):
    data = mysql_data
    app = data["app"]
    barrier = Barrier(2)

    def vender():
        with app.test_client() as client:
            barrier.wait(timeout=10)
            response = client.post("/api/ventas", headers=auth(data["token"]), json={
                "id_cliente": data["cliente"],
                "detalles": [{"id_producto": data["producto"], "cantidad": 1, "precio": "10.00"}],
            })
            return response.status_code, response.get_json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: vender(), range(2)))
    statuses = sorted(status for status, _ in results)
    assert statuses[0] == 201 and statuses[1] in (409, 422)
    venta_id = next(body["id_venta"] for status, body in results if status == 201)

    barrier = Barrier(2)

    def anular():
        with app.test_client() as client:
            barrier.wait(timeout=10)
            return client.post(
                f"/api/ventas/{venta_id}/anulacion", headers=auth(data["token"]),
                json={"motivo": "Prueba de concurrencia E4"},
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: anular(), range(2)))
    assert sorted(results) == [200, 409]
    with app.app_context():
        inventario = db.session.scalar(db.select(Inventario).where(Inventario.id_producto == data["producto"]))
        assert inventario.cantidad == 1


def test_mariadb_compra_con_stock_consumido_no_se_anula(mysql_data):
    data = mysql_data
    app = data["app"]
    with app.test_client() as client:
        compra = client.post("/api/compras", headers=auth(data["token"]), json={
            "id_proveedor": data["proveedor"],
            "detalles": [{"id_producto": data["producto"], "cantidad": 3, "precio": "5.00"}],
        })
        assert compra.status_code == 201
        venta = client.post("/api/ventas", headers=auth(data["token"]), json={
            "id_cliente": data["cliente"],
            "detalles": [{"id_producto": data["producto"], "cantidad": 2, "precio": "10.00"}],
        })
        assert venta.status_code == 201
        anulacion = client.post(
            f"/api/compras/{compra.get_json()['id_compra']}/anulacion",
            headers=auth(data["token"]), json={"motivo": "Prueba E4"},
        )
        assert anulacion.status_code == 409
    with app.app_context():
        inventario = db.session.scalar(db.select(Inventario).where(Inventario.id_producto == data["producto"]))
        assert inventario.cantidad == 2
