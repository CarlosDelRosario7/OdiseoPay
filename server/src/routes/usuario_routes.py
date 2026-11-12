from flask import jsonify, request

from ..extensions import db
from ..models import Usuario
from ..services import usuario_service as service
from ..utils.auth_utils import hash_password, roles_required
from .base_routes import crud_blueprint

service.list_records = service.list_users
service.get_record = service.get_user
usuario_blueprint = crud_blueprint(
    "usuarios",
    "/api/usuarios",
    Usuario,
    service,
    read_roles=("Admin",),
    include_create=False,
)


@usuario_blueprint.post("")
@roles_required("Admin")
def create_user():
    data = request.get_json(silent=True) or {}
    required = ("nombre", "usuario", "contrasena")
    if any(not str(data.get(field, "")).strip() for field in required) or data.get("rol") not in {"Admin", "Vendedor"}:
        return jsonify({"error": "Nombre, usuario, contraseña y rol válido son obligatorios"}), 422

    username = data["usuario"].strip()
    if Usuario.query.filter_by(usuario=username).first() is not None:
        return jsonify({"error": "El nombre de usuario ya existe"}), 409

    user = service.create_user({
        "nombre": data["nombre"].strip(),
        "usuario": username,
        "contrasena": data["contrasena"],
        "rol": data["rol"],
    })
    return jsonify({"id_usuario": user.id_usuario}), 201


@usuario_blueprint.put("/<int:record_id>")
@roles_required("Admin")
def update_user_route(record_id):
    user = service.get_user(record_id)
    data = request.get_json(silent=True) or {}

    if "nombre" in data and str(data["nombre"]).strip():
        user.nombre = str(data["nombre"]).strip()

    if "usuario" in data and str(data["usuario"]).strip():
        new_username = str(data["usuario"]).strip()
        existing = Usuario.query.filter(
            Usuario.usuario == new_username,
            Usuario.id_usuario != user.id_usuario,
        ).first()
        if existing is not None:
            return jsonify({"error": "Ese nombre de usuario ya está en uso"}), 409
        user.usuario = new_username

    if data.get("rol") in {"Admin", "Vendedor"}:
        user.rol = data["rol"]

    if data.get("contrasena"):
        user.contrasena = hash_password(data["contrasena"])

    db.session.commit()
    return jsonify({
        "id_usuario": user.id_usuario,
        "nombre": user.nombre,
        "usuario": user.usuario,
        "rol": user.rol,
    }), 200
