from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config, validate_jwt_secret
from .extensions import db, jwt, migrate
from .utils.security_log import configure_security_logging, log_security_event

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations" / "alembic"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["JWT_SECRET_KEY"] = validate_jwt_secret(
        app.config.get("JWT_SECRET_KEY")
    )

    configure_security_logging()

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db, directory=str(MIGRATIONS_DIR))
    CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGINS"]}})

    from . import models
    from .routes import register_routes

    register_routes(app)

    @app.get("/api/health")
    def health_check():
        return jsonify({"status": "ok"})

    @jwt.unauthorized_loader
    def missing_token(reason):
        log_security_event(
            "auth_token_missing",
            outcome="failure",
            reason=reason,
        )
        return jsonify({"error": "Token de acceso requerido"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        log_security_event(
            "auth_token_invalid",
            outcome="failure",
            reason=reason,
        )
        return jsonify({"error": "Token de acceso inválido"}), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        log_security_event(
            "auth_token_expired",
            outcome="failure",
            user_id=jwt_payload.get("sub"),
        )
        return jsonify({"error": "El token de acceso expiró"}), 401

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        original = getattr(error, "original_exception", error)
        db.session.rollback()
        log_security_event(
            "internal_error",
            outcome="failure",
            error=type(original).__name__,
        )
        return jsonify({"error": "Error interno del servidor"}), 500

    return app
