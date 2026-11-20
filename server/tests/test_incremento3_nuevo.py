"""Pruebas de los módulos NO cubiertos en el incremento 2.

Cubre: venta_service, compra_service, base_routes (crear/eliminar),
serialization_utils, security_log y gemini_service (con mock, DEF-005).
"""

import json
from decimal import Decimal
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.extensions import db
from src.models import (
    Categoria, Cliente, Inventario, Producto, Proveedor,
    Venta, Compra,
)
from src.services import compra_service, venta_service
from src.utils.serialization_utils import serialize_model
from src.utils.security_log import log_security_event, configure_security_logging

from .conftest import auth


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _crear_producto(nombre, cantidad, stock_minimo=5, precio="10.00"):
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
    db.session.add(Inventario(
        id_producto=producto.id_producto,
        cantidad=cantidad,
        stock_minimo=stock_minimo,
        ubicacion="A1",
    ))
    db.session.commit()
    return producto


def _crear_cliente(nombre="Cliente"):
    cliente = Cliente(nombre=nombre, apellido="Prueba", correo=f"{nombre}@test.com")
    db.session.add(cliente)
    db.session.commit()
    return cliente


def _crear_proveedor(nombre="Proveedor"):
    proveedor = Proveedor(nombre=nombre, telefono="", correo="", direccion="")
    db.session.add(proveedor)
    db.session.commit()
    return proveedor


# --------------------------------------------------------------------------
# Unitarias: serialization_utils
# --------------------------------------------------------------------------

def test_serialize_model_oculta_columnas_indicadas(app):
    producto = _crear_producto("Ser", cantidad=1)
    data = serialize_model(producto, ("precio_compra",))
    assert "precio_compra" not in data
    assert "precio_venta" in data


def test_serialize_model_convierte_decimal_a_string(app):
    producto = _crear_producto("Dec", cantidad=1)
    data = serialize_model(producto)
    assert isinstance(data["precio_venta"], str)
    assert data["precio_venta"] == "10.00"


def test_serialize_model_convierte_datetime_a_isoformat(app):
    venta = Venta(id_cliente=1, id_usuario=1)
    db.session.add(venta)
    db.session.commit()
    data = serialize_model(venta)
    assert data["fecha"] is not None
    assert "T" in data["fecha"] or " " in data["fecha"]


# --------------------------------------------------------------------------
# Unitarias: security_log
# --------------------------------------------------------------------------

def test_log_security_event_registra_en_el_log_del_proyecto(app, tmp_path, monkeypatch):
    """El evento queda registrado como una linea JSON valida con los campos enviados."""
    log_security_event("prueba_unit", outcome="ok", detalle="valor")
    ruta_log = Path(__file__).resolve().parents[1] / "logs" / "security.log"
    assert ruta_log.exists()
    lineas = ruta_log.read_text(encoding="utf-8").strip().splitlines()
    registro = json.loads(lineas[-1])
    assert registro["event"] == "prueba_unit"
    assert registro["outcome"] == "ok"
    assert registro["detalle"] == "valor"
    assert "timestamp" in registro


def test_security_logger_reutiliza_la_misma_instancia(app):
    """Llamar dos veces devuelve el mismo logger sin recrear handlers."""
    logger1 = configure_security_logging()
    logger2 = configure_security_logging()
    assert logger1 is logger2
    file_handlers = [h for h in logger1.handlers if isinstance(h, RotatingFileHandler)]
    assert len(file_handlers) == 1


# --------------------------------------------------------------------------
# Unitarias: venta_service / compra_service (reglas de negocio)
# --------------------------------------------------------------------------

def test_venta_sin_cliente_o_detalles_lanza_error(app):
    with pytest.raises(ValueError):
        venta_service.create_sale({}, user_id=1)


def test_compra_sin_proveedor_o_detalles_lanza_error(app):
    with pytest.raises(ValueError):
        compra_service.create_purchase({}, user_id=1)


def test_venta_con_stock_insuficiente_lanza_error(app, admin_user):
    producto = _crear_producto("Poco", cantidad=1)
    cliente = _crear_cliente()
    with pytest.raises(ValueError, match="Stock insuficiente"):
        venta_service.create_sale(
            {
                "id_cliente": cliente.id_cliente,
                "detalles": [{"id_producto": producto.id_producto, "cantidad": 5, "precio": "10.00"}],
            },
            user_id=admin_user.id_usuario,
        )


def test_venta_con_producto_inexistente_lanza_error(app, admin_user):
    cliente = _crear_cliente()
    with pytest.raises(ValueError):
        venta_service.create_sale(
            {
                "id_cliente": cliente.id_cliente,
                "detalles": [{"id_producto": 9999, "cantidad": 1, "precio": "10.00"}],
            },
            user_id=admin_user.id_usuario,
        )


def test_venta_con_cantidad_negativa_lanza_error(app, admin_user):
    producto = _crear_producto("Neg", cantidad=10)
    cliente = _crear_cliente()
    with pytest.raises(ValueError):
        venta_service.create_sale(
            {
                "id_cliente": cliente.id_cliente,
                "detalles": [{"id_producto": producto.id_producto, "cantidad": -2, "precio": "10.00"}],
            },
            user_id=admin_user.id_usuario,
        )


def test_venta_exitosa_descuenta_inventario(app, admin_user):
    producto = _crear_producto("Desc", cantidad=10)
    cliente = _crear_cliente()

    venta = venta_service.create_sale(
        {
            "id_cliente": cliente.id_cliente,
            "detalles": [{"id_producto": producto.id_producto, "cantidad": 4, "precio": "10.00"}],
        },
        user_id=admin_user.id_usuario,
    )

    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 6
    assert len(venta.detalles) == 1
    assert venta.detalles[0].precio == Decimal("10.00")


def test_compra_exitosa_incrementa_inventario(app, admin_user):
    producto = _crear_producto("Inc", cantidad=2)
    proveedor = _crear_proveedor()

    compra = compra_service.create_purchase(
        {
            "id_proveedor": proveedor.id_proveedor,
            "detalles": [{"id_producto": producto.id_producto, "cantidad": 8, "precio": "5.00"}],
        },
        user_id=admin_user.id_usuario,
    )

    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 10
    assert len(compra.detalles) == 1


def test_compra_a_producto_inexistente_lanza_error(app, admin_user):
    proveedor = _crear_proveedor()
    with pytest.raises(ValueError, match="Producto inexistente"):
        compra_service.create_purchase(
            {
                "id_proveedor": proveedor.id_proveedor,
                "detalles": [{"id_producto": 9999, "cantidad": 1, "precio": "5.00"}],
            },
            user_id=admin_user.id_usuario,
        )


def test_compra_con_precio_negativo_lanza_error(app, admin_user):
    producto = _crear_producto("Neg", cantidad=2)
    proveedor = _crear_proveedor()
    with pytest.raises(ValueError):
        compra_service.create_purchase(
            {
                "id_proveedor": proveedor.id_proveedor,
                "detalles": [{"id_producto": producto.id_producto, "cantidad": 1, "precio": "-1.00"}],
            },
            user_id=admin_user.id_usuario,
        )


# --------------------------------------------------------------------------
# Integración: endpoints de ventas y compras
# --------------------------------------------------------------------------

def test_ventas_requiere_token(client):
    assert client.get("/api/ventas").status_code == 401


def test_ventas_lista_vacia(client, admin_token):
    response = client.get("/api/ventas", headers=auth(admin_token))
    body = response.get_json()
    assert response.status_code == 200
    assert body["items"] == []
    assert body["total"] == 0


def test_ventas_requiere_autenticacion_para_crear(client):
    response = client.post(
        "/api/ventas",
        json={"id_cliente": 1, "detalles": []},
    )
    assert response.status_code == 401


def test_crear_venta_endpoint_exitoso(client, admin_token, admin_user):
    producto = _crear_producto("Venta", cantidad=10)
    cliente = _crear_cliente()

    response = client.post(
        "/api/ventas",
        json={
            "id_cliente": cliente.id_cliente,
            "detalles": [{"id_producto": producto.id_producto, "cantidad": 3, "precio": "10.00"}],
        },
        headers=auth(admin_token),
    )

    assert response.status_code == 201
    assert response.get_json()["id_venta"] is not None
    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 7


def test_crear_venta_endpoint_sin_cliente_devuelve_422(client, admin_token):
    producto = _crear_producto("V", cantidad=10)
    response = client.post(
        "/api/ventas",
        json={"detalles": [{"id_producto": producto.id_producto, "cantidad": 1, "precio": "10.00"}]},
        headers=auth(admin_token),
    )
    assert response.status_code == 422


def test_crear_venta_endpoint_stock_insuficiente_devuelve_422(client, admin_token):
    producto = _crear_producto("Stock", cantidad=1)
    cliente = _crear_cliente()
    response = client.post(
        "/api/ventas",
        json={
            "id_cliente": cliente.id_cliente,
            "detalles": [{"id_producto": producto.id_producto, "cantidad": 99, "precio": "10.00"}],
        },
        headers=auth(admin_token),
    )
    assert response.status_code == 422
    assert "Stock insuficiente" in response.get_json()["error"]


def test_compras_requiere_token(client):
    assert client.get("/api/compras").status_code == 401


def test_crear_compra_endpoint_exitoso(client, admin_token, admin_user):
    producto = _crear_producto("Compra", cantidad=2)
    proveedor = _crear_proveedor()

    response = client.post(
        "/api/compras",
        json={
            "id_proveedor": proveedor.id_proveedor,
            "detalles": [{"id_producto": producto.id_producto, "cantidad": 5, "precio": "5.00"}],
        },
        headers=auth(admin_token),
    )

    assert response.status_code == 201
    assert response.get_json()["id_compra"] is not None
    db.session.refresh(producto.inventario)
    assert producto.inventario.cantidad == 7


def test_crear_compra_endpoint_producto_inexistente_devuelve_422(client, admin_token):
    proveedor = _crear_proveedor()
    response = client.post(
        "/api/compras",
        json={
            "id_proveedor": proveedor.id_proveedor,
            "detalles": [{"id_producto": 9999, "cantidad": 1, "precio": "5.00"}],
        },
        headers=auth(admin_token),
    )
    assert response.status_code == 422


# --------------------------------------------------------------------------
# Integración: base_routes (crear y eliminar genéricos, con productos)
# --------------------------------------------------------------------------

def test_crear_producto_generico_como_admin(client, admin_token):
    categoria = Categoria(nombre="Cat", descripcion="")
    proveedor = Proveedor(nombre="Prov", telefono="", correo="", direccion="")
    db.session.add_all([categoria, proveedor])
    db.session.commit()

    response = client.post(
        "/api/productos",
        json={
            "nombre": "ProductoNuevo",
            "descripcion": "",
            "precio_compra": "5.00",
            "precio_venta": "12.00",
            "id_categoria": categoria.id_categoria,
            "id_proveedor": proveedor.id_proveedor,
        },
        headers=auth(admin_token),
    )
    assert response.status_code == 201
    assert response.get_json()["nombre"] == "ProductoNuevo"


def test_crear_producto_generico_campos_faltantes(client, admin_token):
    response = client.post(
        "/api/productos",
        json={"nombre": "Incompleto"},
        headers=auth(admin_token),
    )
    assert response.status_code == 422
    assert "fields" in response.get_json()


def test_crear_producto_generico_como_vendedor_prohibido(client, vendedor_token):
    response = client.post(
        "/api/productos",
        json={"nombre": "X"},
        headers=auth(vendedor_token),
    )
    assert response.status_code == 403


def test_eliminar_producto_con_inventario_devuelve_409_y_no_lo_borra(client, admin_token):
    """Borrar un producto con inventario (FK activa) se rechaza con 409."""
    producto = _crear_producto("ConInv", cantidad=5)
    response = client.delete(
        f"/api/productos/{producto.id_producto}",
        headers=auth(admin_token),
    )
    assert response.status_code == 409
    assert "relacionados" in response.get_json()["error"]
    db.session.refresh(producto)
    assert producto.id_producto is not None  # sigue existiendo





def test_eliminar_producto_inexistente_devuelve_404(client, admin_token):
    response = client.delete("/api/productos/9999", headers=auth(admin_token))
    assert response.status_code == 404


# --------------------------------------------------------------------------
# Integración: gemini_service con mock (DEF-005)
# --------------------------------------------------------------------------

def test_gemini_sin_api_key_lanza_error(app):
    from src.services import gemini_service
    with pytest.raises(RuntimeError):
        gemini_service.analizar_inventario([])


def test_gemini_sin_productos_devuelve_mensaje(app):
    from src.services import gemini_service
    app.config["GEMINI_API_KEY"] = "fake-key"
    assert gemini_service.analizar_inventario([]) == "No hay información de inventario disponible para analizar."


def test_gemini_con_producto_incluye_datos_en_prompt(app):
    """El prompt enviado a Gemini contiene los datos del inventario."""
    from src.services import gemini_service
    app.config["GEMINI_API_KEY"] = "fake-key"
    producto = _crear_producto("Gem", cantidad=2, stock_minimo=5)

    mock_client = MagicMock()
    mock_client.interactions.create.return_value.output_text = "Analisis simulado"
    with patch("google.genai.Client", return_value=mock_client):
        resultado = gemini_service.analizar_inventario([producto])

    assert resultado == "Analisis simulado"
    prompt = mock_client.interactions.create.call_args.kwargs["input"]
    assert "Gem" in prompt
    assert "cantidad: 2" in prompt
    assert "stock mínimo: 5" in prompt


def test_gemini_ignora_productos_sin_inventario(app):
    """Los productos sin inventario no se incluyen en el prompt."""
    from src.services import gemini_service
    app.config["GEMINI_API_KEY"] = "fake-key"
    categoria = Categoria(nombre="Cat", descripcion="")
    proveedor = Proveedor(nombre="Prov", telefono="", correo="", direccion="")
    db.session.add_all([categoria, proveedor])
    db.session.flush()
    producto = Producto(
        nombre="SinInv", descripcion="", precio_compra="1.00", precio_venta="2.00",
        id_categoria=categoria.id_categoria, id_proveedor=proveedor.id_proveedor,
    )
    db.session.add(producto)
    db.session.commit()

    mock_client = MagicMock()
    mock_client.interactions.create.return_value.output_text = "ok"
    with patch("google.genai.Client", return_value=mock_client):
        resultado = gemini_service.analizar_inventario([producto])

    # El producto sin inventario se omite: no hay datos -> mensaje de vacio
    assert resultado == "No hay información de inventario disponible para analizar."
    mock_client.interactions.create.assert_not_called()
