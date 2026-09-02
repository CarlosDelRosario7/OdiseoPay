from ..models import Compra
from flask import jsonify, request

from ..services import compra_service as service
from ..utils.auth_utils import current_user_id, roles_required
from ..utils.serialization_utils import serialize_model
from .base_routes import crud_blueprint

service.list_records = service.list_purchases
service.get_record = service.get_purchase
compra_blueprint = crud_blueprint("compras", "/api/compras", Compra, service, read_roles=("Admin",), include_create=False)


@compra_blueprint.post("")
@roles_required("Admin")
def create_purchase():
	try:
		purchase = service.create_purchase(request.get_json(silent=True) or {}, current_user_id())
	except (KeyError, TypeError, ValueError) as error:
		return jsonify({"error": str(error)}), 422
	return jsonify(serialize_model(purchase)), 201
