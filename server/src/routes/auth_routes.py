import jwt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db, limiter
from ..models import Usuario
from ..services.usuario_service import create_user
from ..utils.auth0_utils import (
    is_auth0_configured,
    validate_auth0_token,
)
from ..utils.auth_utils import (
    create_token,
    current_user_id,
    verify_password,
)
from ..utils.security_log import log_security_event


auth_blueprint = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)

AUTH0_NOT_CONFIGURED = (
    "Auth0 no está configurado en el servidor. "
    "Revisa AUTH0_DOMAIN y AUTH0_AUDIENCE en server/.env."
)


def _auth0_provider(auth0_sub: str | None) -> str | None:
    if not auth0_sub:
        return None

    provider = auth0_sub.split("|", 1)[0]

    return {
        "google-oauth2": "Google",
        "facebook": "Facebook",
        "auth0": "Auth0",
    }.get(provider, provider)


def _serialize_user(user: Usuario) -> dict:
    return {
        "id_usuario": user.id_usuario,
        "nombre": user.nombre,
        "usuario": user.usuario,
        "rol": user.rol,
        "auth0_sub": user.auth0_sub,
        "auth0_provider": _auth0_provider(user.auth0_sub),
    }


def _bearer_token() -> str:
    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        return ""

    return authorization.removeprefix("Bearer ").strip()


def _auth0_error_response(error: Exception):
    """Traduce errores de Auth0 a respuestas HTTP consistentes."""
    if isinstance(error, RuntimeError):
        return jsonify({"error": AUTH0_NOT_CONFIGURED}), 503

    if isinstance(error, jwt.ExpiredSignatureError):
        return jsonify({"error": "El token de Auth0 expiró."}), 401

    if isinstance(error, jwt.InvalidTokenError):
        return jsonify({"error": "Token de Auth0 inválido."}), 401

    return jsonify({
        "error": "No se pudo validar la cuenta de Auth0."
    }), 401


@auth_blueprint.post("/login")
@limiter.limit("5 per minute", deduct_when=lambda response: response.status_code == 401)
def login():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}
    username = data.get("usuario")
    password = data.get("contrasena")
    user = (
        Usuario.query.filter_by(usuario=username).first()
        if isinstance(username, str) and isinstance(password, str)
        else None
    )

    if user is None or not verify_password(
        user.contrasena,
        password,
    ):
        log_security_event(
            "login_failed",
            outcome="failure",
            usuario=str(data.get("usuario"))[:80],
            reason="invalid_credentials",
        )
        return jsonify({
            "error": "Credenciales inválidas"
        }), 401

    log_security_event(
        "login_succeeded",
        outcome="success",
        user_id=user.id_usuario,
        usuario=user.usuario,
        rol=user.rol,
    )

    return jsonify({
        "access_token": create_token(user),
        **_serialize_user(user),
    }), 200


@auth_blueprint.post("/registro")
def register():
    data = request.get_json(silent=True) or {}

    if data.get("rol") not in {"Admin", "Vendedor"}:
        log_security_event(
            "bootstrap_registration_rejected",
            outcome="failure",
            usuario=str(data.get("usuario"))[:80],
            reason="invalid_role",
        )
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
        log_security_event(
            "bootstrap_registration_rejected",
            outcome="failure",
            usuario=str(data.get("usuario"))[:80],
            reason="first_user_must_be_admin",
        )
        return jsonify({
            "error": "El primer usuario debe ser Admin"
        }), 422

    if has_users:
        log_security_event(
            "bootstrap_registration_rejected",
            outcome="failure",
            usuario=str(data.get("usuario"))[:80],
            reason="bootstrap_already_completed",
        )
        return jsonify({
            "error": (
                "Solo un administrador puede registrar usuarios"
            )
        }), 401

    if any(not isinstance(data.get(field), str) or not data[field].strip()
           for field in ("nombre", "usuario", "contrasena")):
        return jsonify({"error": "Nombre, usuario y contraseña son obligatorios"}), 422

    user = create_user(data)

    log_security_event(
        "bootstrap_admin_created",
        outcome="success",
        user_id=user.id_usuario,
        usuario=user.usuario,
    )

    return jsonify({
        "id_usuario": user.id_usuario
    }), 201


@auth_blueprint.post("/auth0/login")
def auth0_login():
    token = _bearer_token()

    if not token:
        log_security_event(
            "auth0_login_failed",
            outcome="failure",
            reason="missing_bearer_token",
        )
        return jsonify({
            "error": "Bearer token requerido"
        }), 401

    if not is_auth0_configured():
        return jsonify({"error": AUTH0_NOT_CONFIGURED}), 503

    try:
        payload = validate_auth0_token(token)

        auth0_sub = payload.get("sub")

        if not auth0_sub:
            return jsonify({
                "error": "El token de Auth0 no contiene el identificador sub."
            }), 401

        user = Usuario.query.filter_by(
            auth0_sub=auth0_sub
        ).first()

        if user is None:
            log_security_event(
                "auth0_login_failed",
                outcome="failure",
                auth0_sub=auth0_sub,
                reason="unlinked_account",
            )
            return jsonify({
                "error": (
                    "Esta cuenta social todavía no está vinculada a un "
                    "usuario de OdiseoPay. Inicia sesión con tu usuario y "
                    "contraseña y vincúlala desde el menú lateral."
                )
            }), 403

        log_security_event(
            "auth0_login_succeeded",
            outcome="success",
            user_id=user.id_usuario,
            auth0_sub=auth0_sub,
            rol=user.rol,
        )

        return jsonify({
            "access_token": create_token(user),
            **_serialize_user(user),
        }), 200

    except Exception as error:
        log_security_event(
            "auth0_login_failed",
            outcome="failure",
            reason=type(error).__name__,
        )
        return _auth0_error_response(error)


@auth_blueprint.post("/auth0/vincular")
@jwt_required()
def link_auth0_account():
    if not is_auth0_configured():
        return jsonify({"error": AUTH0_NOT_CONFIGURED}), 503

    data = request.get_json(silent=True) or {}
    token = (data.get("auth0_token") or "").strip()

    if not token:
        log_security_event(
            "auth0_link_failed",
            outcome="failure",
            reason="missing_auth0_token",
        )
        return jsonify({
            "error": "El token de Auth0 es requerido para vincular la cuenta."
        }), 422

    user = db.session.get(Usuario, current_user_id())

    if user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    try:
        payload = validate_auth0_token(token)
        auth0_sub = payload.get("sub")

        if not auth0_sub:
            return jsonify({
                "error": "El token de Auth0 no contiene el identificador sub."
            }), 401

        if user.auth0_sub == auth0_sub:
            log_security_event(
                "auth0_link_noop",
                outcome="info",
                user_id=user.id_usuario,
                auth0_sub=auth0_sub,
                reason="already_linked_to_same_account",
            )
            return jsonify({
                "auth0_sub": user.auth0_sub,
                "auth0_provider": _auth0_provider(user.auth0_sub),
                "message": "Esta cuenta social ya está vinculada a tu usuario.",
            }), 200

        if user.auth0_sub:
            log_security_event(
                "auth0_link_rejected",
                outcome="failure",
                user_id=user.id_usuario,
                auth0_sub=auth0_sub,
                reason="user_already_has_social_account",
            )
            return jsonify({
                "error": (
                    "Tu usuario ya tiene una cuenta social vinculada "
                    f"({_auth0_provider(user.auth0_sub)}). Desvincúlala antes "
                    "de vincular otra."
                ),
                "auth0_sub": user.auth0_sub,
                "auth0_provider": _auth0_provider(user.auth0_sub),
            }), 409

        existing = Usuario.query.filter(
            Usuario.auth0_sub == auth0_sub,
            Usuario.id_usuario != user.id_usuario,
        ).first()

        if existing is not None:
            log_security_event(
                "auth0_link_rejected",
                outcome="failure",
                user_id=user.id_usuario,
                auth0_sub=auth0_sub,
                reason="social_account_in_use",
            )
            return jsonify({
                "error": (
                    "Esa cuenta social ya está vinculada a otro usuario "
                    "de OdiseoPay."
                )
            }), 409

        user.auth0_sub = auth0_sub
        db.session.commit()

        log_security_event(
            "auth0_link_succeeded",
            outcome="success",
            user_id=user.id_usuario,
            auth0_sub=auth0_sub,
        )

        return jsonify({
            "auth0_sub": user.auth0_sub,
            "auth0_provider": _auth0_provider(user.auth0_sub),
            "message": "Cuenta social vinculada correctamente.",
        }), 200

    except IntegrityError:
        db.session.rollback()
        log_security_event(
            "auth0_link_rejected",
            outcome="failure",
            user_id=user.id_usuario,
            reason="integrity_error",
        )
        return jsonify({
            "error": (
                "Esa cuenta social ya está vinculada a otro usuario "
                "de OdiseoPay."
            )
        }), 409

    except Exception as error:
        db.session.rollback()
        log_security_event(
            "auth0_link_failed",
            outcome="failure",
            user_id=user.id_usuario,
            reason=type(error).__name__,
        )
        return _auth0_error_response(error)


@auth_blueprint.delete("/auth0/vincular")
@jwt_required()
def unlink_auth0_account():
    user = db.session.get(Usuario, current_user_id())

    if user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if not user.auth0_sub:
        return jsonify({
            "message": "Tu usuario no tiene una cuenta social vinculada."
        }), 200

    user.auth0_sub = None
    db.session.commit()

    log_security_event(
        "auth0_unlink_succeeded",
        outcome="success",
        user_id=user.id_usuario,
    )

    return "", 204
