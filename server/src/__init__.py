from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .extensions import db, jwt, migrate

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations" / "alembic"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor"}), 500

    return app
