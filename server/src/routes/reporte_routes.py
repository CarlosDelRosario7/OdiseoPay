from flask import Blueprint, jsonify, request

from ..services import reporte_service as service
from ..utils.auth_utils import roles_required
from ..utils.serialization_utils import serialize_model

reporte_blueprint = Blueprint("reportes", __name__, url_prefix="/api/reportes")


def _umbral_from_request():
    """Lee el parametro de umbral ajustable desde la peticion (query o JSON)."""
    raw = request.args.get("umbral")
    if raw is None and request.is_json:
        raw = (request.get_json(silent=True) or {}).get("umbral")
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return "invalid"
    return value if value >= 0 else "invalid"


def _serialize_bajo_stock(item):
    data = serialize_model(item)
    data["nombre_producto"] = item.producto.nombre if item.producto else None
    data["precio_venta"] = str(item.producto.precio_venta) if item.producto else None
    data["faltante"] = max(item.stock_minimo - item.cantidad, 0)
    return data


@reporte_blueprint.get("/bajo-stock")
@roles_required("Admin", "Vendedor")
def list_bajo_stock():
    umbral = _umbral_from_request()
    if umbral == "invalid":
        return jsonify({"error": "El umbral debe ser un entero mayor o igual a 0"}), 422
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    pagination = service.bajo_stock(umbral=umbral, page=page, per_page=per_page)
    return jsonify({
        "items": [_serialize_bajo_stock(item) for item in pagination.items],
        "umbral": umbral,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    })


@reporte_blueprint.get("/bajo-stock/resumen")
@roles_required("Admin", "Vendedor")
def resumen_bajo_stock():
    umbral = _umbral_from_request()
    if umbral == "invalid":
        return jsonify({"error": "El umbral debe ser un entero mayor o igual a 0"}), 422
    return jsonify({"umbral": umbral, "total": service.resumen_bajo_stock(umbral=umbral)})


@reporte_blueprint.patch("/bajo-stock/<int:id_producto>")
@roles_required("Admin")
def update_stock_minimo(id_producto):
    """Ajusta el stock minimo (umbral) propio de un producto."""
    data = request.get_json(silent=True) or {}
    valor = data.get("stock_minimo")
    if not isinstance(valor, int) or isinstance(valor, bool) or valor < 0:
        return jsonify({"error": "stock_minimo debe ser un entero mayor o igual a 0"}), 422
    inventario = service.actualizar_stock_minimo(id_producto, valor)
    if inventario is None:
        return jsonify({"error": "El producto no tiene registro de inventario"}), 404
    return jsonify(serialize_model(inventario))
