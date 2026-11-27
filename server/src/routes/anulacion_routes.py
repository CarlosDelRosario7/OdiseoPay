"""Gestión de la respuesta de las anulaciones protegidas."""

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError, OperationalError

from ..extensions import db
from ..services.anulacion_service import ConflictoAnulacion, anular, serializar
from ..utils.auth_utils import current_user_id


def anular_operacion(tipo, identificador):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Debe indicar el motivo de la anulación"}), 422
    try:
        registro = anular(tipo, identificador, current_user_id(), data.get("motivo"))
        return jsonify(serializar(registro)), 200
    except LookupError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 404
    except ConflictoAnulacion as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 409
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 422
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "La operación ya fue anulada o presenta un conflicto de datos"}), 409
    except OperationalError as error:
        db.session.rollback()
        if error.orig.args and error.orig.args[0] in (1020, 1205, 1213):
            return jsonify({"error": "Conflicto de inventario; inténtelo nuevamente"}), 409
        raise
