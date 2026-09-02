from flask import Blueprint, jsonify, request

from ..models import Usuario
from ..extensions import db
from ..services.usuario_service import create_user
from ..utils.auth_utils import create_token, verify_password

auth_blueprint = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_blueprint.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = Usuario.query.filter_by(usuario=data.get("usuario")).first()
    if user is None or not verify_password(user.contrasena, data.get("contrasena", "")):
        return jsonify({"error": "Credenciales inválidas"}), 401
    return jsonify({"access_token": create_token(user), "usuario": user.usuario, "rol": user.rol})


@auth_blueprint.post("/registro")
def register():
    data = request.get_json(silent=True) or {}
    if data.get("rol") not in {"Admin", "Vendedor"}:
        return jsonify({"error": "El rol debe ser Admin o Vendedor"}), 422
    has_users = db.session.scalar(db.select(Usuario.id_usuario).limit(1)) is not None
    if not has_users and data.get("rol") != "Admin":
        return jsonify({"error": "El primer usuario debe ser Admin"}), 422
    if has_users:
        return jsonify({"error": "Solo un administrador puede registrar usuarios"}), 401
    return jsonify({"id_usuario": create_user(data).id_usuario}), 201
