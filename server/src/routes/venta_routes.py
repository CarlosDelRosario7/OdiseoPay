from ..models import Venta
from flask import jsonify, request

from ..services import venta_service as service
from ..utils.auth_utils import current_user_id, roles_required
from ..utils.serialization_utils import serialize_model
from .base_routes import crud_blueprint

service.list_records = service.list_sales
service.get_record = service.get_sale
venta_blueprint = crud_blueprint("ventas", "/api/ventas", Venta, service, ("Admin", "Vendedor"), include_create=False)


@venta_blueprint.post("")
@roles_required("Admin", "Vendedor")
def create_sale():
	try:
		sale = service.create_sale(request.get_json(silent=True) or {}, current_user_id())
	except (KeyError, TypeError, ValueError) as error:
		return jsonify({"error": str(error)}), 422
	return jsonify(serialize_model(sale)), 201
