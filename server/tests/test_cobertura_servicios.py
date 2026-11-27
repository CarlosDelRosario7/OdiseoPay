"""Casos límite de servicios y del endpoint de análisis de inventario."""

import pytest

from src.extensions import db
from src.models import DetalleVenta, Venta
from src.services.anulacion_service import anular

from .conftest import auth
from .test_incremento3_nuevo import _crear_cliente, _crear_producto


def test_analisis_inventario_sin_productos(client, admin_token):
    response = client.post("/api/ia/inventario", headers=auth(admin_token))
    assert response.status_code == 404
    assert "No hay productos" in response.get_json()["error"]


@pytest.mark.parametrize(
    ("resultado", "status", "field"),
    [
        ("Reponer mercancía", 200, "analisis"),
        (RuntimeError("Servicio no configurado"), 503, "error"),
        (ValueError("detalle interno"), 502, "error"),
    ],
)
def test_analisis_inventario_respuestas_y_errores(client, admin_token, monkeypatch, resultado, status, field):
    _crear_producto("IA", cantidad=3)

    def fake_analizar(productos):
        assert len(productos) == 1
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    monkeypatch.setattr("src.routes.ia_routes.analizar_inventario", fake_analizar)
    response = client.post("/api/ia/inventario", headers=auth(admin_token))
    assert response.status_code == status
    assert response.get_json()[field]
    if status == 200:
        assert response.get_json()["productos_analizados"] == 1
        assert response.get_json()["analisis"] == "Reponer mercancía"
    if status == 502:
        assert "detalle interno" not in response.get_json()["error"]


def test_anular_rechaza_tipo_y_usuario_inexistentes(app):
    with pytest.raises(ValueError, match="Tipo"):
        anular("OTRO", 1, 1, "Prueba")
    with pytest.raises(ValueError, match="Usuario"):
        anular("VENTA", 1, 9999, "Prueba")


def test_anulacion_de_venta_sin_detalles_es_rechazada(client, admin_token, admin_user):
    cliente = _crear_cliente()
    venta = Venta(id_cliente=cliente.id_cliente, id_usuario=admin_user.id_usuario)
    db.session.add(venta)
    db.session.commit()
    response = client.post(f"/api/ventas/{venta.id_venta}/anulacion", headers=auth(admin_token), json={"motivo": "Prueba"})
    assert response.status_code == 409
    assert "detalles" in response.get_json()["error"]


def test_anulacion_de_venta_sin_inventario_es_rechazada(client, admin_token, admin_user):
    producto = _crear_producto("SinInventario", cantidad=1)
    cliente = _crear_cliente()
    venta = Venta(id_cliente=cliente.id_cliente, id_usuario=admin_user.id_usuario)
    venta.detalles.append(DetalleVenta(id_producto=producto.id_producto, cantidad=1, precio="10.00"))
    db.session.add(venta)
    db.session.commit()
    db.session.delete(producto.inventario)
    db.session.commit()
    response = client.post(f"/api/ventas/{venta.id_venta}/anulacion", headers=auth(admin_token), json={"motivo": "Prueba"})
    assert response.status_code == 409
    assert "inventario" in response.get_json()["error"]


def test_venta_rechaza_precio_negativo_de_catalogo(client, admin_token):
    producto = _crear_producto("PrecioNegativo", cantidad=2, precio="-1.00")
    cliente = _crear_cliente()
    response = client.post("/api/ventas", headers=auth(admin_token), json={
        "id_cliente": cliente.id_cliente,
        "detalles": [{"id_producto": producto.id_producto, "cantidad": 1}],
    })
    assert response.status_code == 422
    assert "Precio de catálogo" in response.get_json()["error"]


def test_compra_rechaza_proveedor_inexistente(client, admin_token):
    response = client.post("/api/compras", headers=auth(admin_token), json={
        "id_proveedor": 99999,
        "detalles": [{"id_producto": 1, "cantidad": 1, "precio": "1.00"}],
    })
    assert response.status_code == 422
    assert "Proveedor inexistente" in response.get_json()["error"]
