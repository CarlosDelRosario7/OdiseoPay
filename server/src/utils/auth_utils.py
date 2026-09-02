from functools import wraps

from flask import jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def create_token(user):
    return create_access_token(identity=str(user.id_usuario), additional_claims={"rol": user.rol})


def current_user_id():
    return int(get_jwt_identity())


def roles_required(*roles):
    def decorator(function):
        @wraps(function)
        @jwt_required()
        def wrapper(*args, **kwargs):
            if get_jwt().get("rol") not in roles:
                return jsonify({"error": "No tienes permisos para esta operación"}), 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


def login_required(function):
    return jwt_required()(function)
