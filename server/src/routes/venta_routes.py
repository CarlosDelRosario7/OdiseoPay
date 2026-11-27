from ..models import Venta
from decimal import InvalidOperation
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError, OperationalError

from ..services import venta_service as service
from ..extensions import db
from ..utils.auth_utils import current_user_id, roles_required
from ..utils.serialization_utils import serialize_model
from .base_routes import crud_blueprint
from .anulacion_routes import anular_operacion

service.list_records = service.list_sales
service.get_record = service.get_sale
venta_blueprint = crud_blueprint("ventas", "/api/ventas", Venta, service, ("Admin", "Vendedor"), include_create=False)

@venta_blueprint.post("/<int:identifier>/anulacion")
@roles_required("Admin")
def cancel_sale(identifier):
	return anular_operacion("VENTA", identifier)


@venta_blueprint.post("")
@roles_required("Admin", "Vendedor")
def create_sale():
	try:
		sale = service.create_sale(request.get_json(silent=True) or {}, current_user_id())
	except (KeyError, TypeError, ValueError, InvalidOperation) as error:
		db.session.rollback()
		message = str(error) if isinstance(error, ValueError) else "Datos de venta inválidos"
		return jsonify({"error": message}), 422
	except IntegrityError:
		db.session.rollback()
		return jsonify({"error": "No se pudo registrar la venta por un conflicto de datos"}), 409
	except OperationalError as error:
		db.session.rollback()
		if error.orig.args and error.orig.args[0] in (1020, 1205, 1213):
			return jsonify({"error": "Conflicto de inventario; inténtelo nuevamente"}), 409
		raise
	return jsonify(serialize_model(sale)), 201
