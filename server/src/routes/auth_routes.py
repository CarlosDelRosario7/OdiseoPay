from flask import Blueprint, jsonify, request
import jwt

from ..models import Usuario
from ..extensions import db
from ..services.usuario_service import create_user
from ..utils.auth_utils import create_token, verify_password
from ..utils.auth0_utils import validate_auth0_token


auth_blueprint = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


@auth_blueprint.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    user = Usuario.query.filter_by(
        usuario=data.get("usuario")
    ).first()

    if user is None or not verify_password(
        user.contrasena,
        data.get("contrasena", ""),
    ):
        return jsonify({
            "error": "Credenciales inválidas"
        }), 401

    return jsonify({
        "access_token": create_token(user),
        "id_usuario": user.id_usuario,
        "nombre": user.nombre,
        "usuario": user.usuario,
        "rol": user.rol,
    }), 200


@auth_blueprint.post("/registro")
def register():
    data = request.get_json(silent=True) or {}

    if data.get("rol") not in {"Admin", "Vendedor"}:
        return jsonify({
            "error": "El rol debe ser Admin o Vendedor"
        }), 422

    has_users = (
        db.session.scalar(
            db.select(Usuario.id_usuario).limit(1)
        )
        is not None
    )

    if not has_users and data.get("rol") != "Admin":
        return jsonify({
            "error": "El primer usuario debe ser Admin"
        }), 422

    if has_users:
        return jsonify({
            "error": (
                "Solo un administrador puede registrar usuarios"
            )
        }), 401

    user = create_user(data)

    return jsonify({
        "id_usuario": user.id_usuario
    }), 201


@auth_blueprint.post("/auth0/login")
def auth0_login():
    authorization = request.headers.get(
        "Authorization",
        "",
    )

    if not authorization.startswith("Bearer "):
        return jsonify({
            "error": "Bearer token requerido"
        }), 401

    token = authorization.removeprefix(
        "Bearer "
    ).strip()

    if not token:
        return jsonify({
            "error": "Bearer token requerido"
        }), 401

    try:
        payload = validate_auth0_token(token)

        auth0_sub = payload.get("sub")

        if not auth0_sub:
            return jsonify({
                "error": "El token no contiene sub"
            }), 401

        user = Usuario.query.filter_by(
            auth0_sub=auth0_sub
        ).first()

        if user is None:
            return jsonify({
                "error": (
                    "La cuenta de Auth0 no está vinculada "
                    "a un usuario de OdiseoPay"
                )
            }), 403

        return jsonify({
            "access_token": create_token(user),
            "id_usuario": user.id_usuario,
            "nombre": user.nombre,
            "usuario": user.usuario,
            "rol": user.rol,
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({
            "error": "El token de Auth0 expiró"
        }), 401

    except jwt.InvalidTokenError:
        return jsonify({
            "error": "Token de Auth0 inválido"
        }), 401

    except Exception:
        return jsonify({
            "error": (
                "No se pudo iniciar sesión con Auth0"
            )
        }), 500