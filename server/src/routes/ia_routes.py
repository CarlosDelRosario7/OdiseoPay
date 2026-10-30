from flask import Blueprint, jsonify

from ..models import Producto
from ..services.gemini_service import analizar_inventario
from ..utils.auth_utils import roles_required


ia_blueprint = Blueprint(
    "ia",
    __name__,
    url_prefix="/api/ia",
)


@ia_blueprint.post("/inventario")
@roles_required("Admin")
def analizar_inventario_route():
    productos = Producto.query.all()

    if not productos:
        return jsonify({
            "error": "No hay productos disponibles para analizar."
        }), 404

    try:
        analisis = analizar_inventario(productos)

        return jsonify({
            "analisis": analisis,
            "productos_analizados": len(productos),
        }), 200

    except RuntimeError as error:
        return jsonify({
            "error": str(error)
        }), 503

    except Exception:
        return jsonify({
            "error": "No se pudo completar el análisis con Gemini."
        }), 502