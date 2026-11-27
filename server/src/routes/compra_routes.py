from ..models import Compra
from decimal import InvalidOperation
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError, OperationalError

from ..extensions import db
from ..services import compra_service as service
from ..utils.auth_utils import current_user_id, roles_required
from ..utils.serialization_utils import serialize_model
from .base_routes import crud_blueprint
from .anulacion_routes import anular_operacion

service.list_records = service.list_purchases
service.get_record = service.get_purchase
compra_blueprint = crud_blueprint("compras", "/api/compras", Compra, service, read_roles=("Admin",), include_create=False)

@compra_blueprint.post("/<int:identifier>/anulacion")
@roles_required("Admin")
def cancel_purchase(identifier):
	return anular_operacion("COMPRA", identifier)


@compra_blueprint.post("")
@roles_required("Admin")
def create_purchase():
	try:
		purchase = service.create_purchase(request.get_json(silent=True) or {}, current_user_id())
	except (KeyError, TypeError, ValueError, InvalidOperation) as error:
		db.session.rollback()
		message = str(error) if isinstance(error, ValueError) else "Datos de compra inválidos"
		return jsonify({"error": message}), 422
	except IntegrityError:
		db.session.rollback()
		return jsonify({"error": "No se pudo registrar la compra por un conflicto de datos"}), 409
	except OperationalError as error:
		db.session.rollback()
		if error.orig.args and error.orig.args[0] in (1020, 1205, 1213):
			return jsonify({"error": "Conflicto de inventario; inténtelo nuevamente"}), 409
		raise
	return jsonify(serialize_model(purchase)), 201
