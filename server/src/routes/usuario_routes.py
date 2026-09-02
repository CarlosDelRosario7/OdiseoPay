from flask import jsonify, request

from ..models import Usuario
from ..services import usuario_service as service
from ..utils.auth_utils import roles_required
from .base_routes import crud_blueprint

service.list_records = service.list_users
service.get_record = service.get_user
usuario_blueprint = crud_blueprint("usuarios", "/api/usuarios", Usuario, service, read_roles=("Admin",), include_create=False)


@usuario_blueprint.post("")
@roles_required("Admin")
def create_user():
	data = request.get_json(silent=True) or {}
	required = ("nombre", "usuario", "contrasena")
	if any(not data.get(field) for field in required) or data.get("rol") not in {"Admin", "Vendedor"}:
		return jsonify({"error": "Nombre, usuario, contraseña y rol válido son obligatorios"}), 422
	return jsonify({"id_usuario": service.create_user(data).id_usuario}), 201
