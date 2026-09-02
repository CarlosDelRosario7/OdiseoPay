from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..utils.auth_utils import roles_required
from ..utils.serialization_utils import serialize_model


def crud_blueprint(name, url_prefix, model, service, write_roles=("Admin",), read_roles=("Admin", "Vendedor"), include_create=True):
    blueprint = Blueprint(name, __name__, url_prefix=url_prefix)

    @blueprint.get("")
    @roles_required(*read_roles)
    def list_items():
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        pagination = service.list_records(page, per_page)
        return jsonify({"items": [serialize_model(item, ("contraseña",)) for item in pagination.items], "page": pagination.page, "per_page": pagination.per_page, "total": pagination.total, "pages": pagination.pages})

    @blueprint.get("/<int:identifier>")
    @roles_required(*read_roles)
    def get_item(identifier):
        return jsonify(serialize_model(service.get_record(identifier), ("contraseña",)))

    if include_create:
        @blueprint.post("")
        @roles_required(*write_roles)
        def create_item():
            data = request.get_json(silent=True) or {}
            allowed = {column.name for column in model.__table__.columns if not column.primary_key}
            values = {key: value for key, value in data.items() if key in allowed}
            missing = [column.name for column in model.__table__.columns if column.name in allowed and column.nullable is False and column.default is None and column.server_default is None and column.name not in values]
            if missing:
                return jsonify({"error": "Faltan campos obligatorios", "fields": missing}), 422
            item = model(**values)
            db.session.add(item)
            db.session.commit()
            return jsonify(serialize_model(item, ("contraseña",))), 201

    @blueprint.patch("/<int:identifier>")
    @roles_required(*write_roles)
    def update_item(identifier):
        item = service.get_record(identifier)
        data = request.get_json(silent=True) or {}
        columns = {column.name: column for column in model.__table__.columns if not column.primary_key}
        invalid_nulls = [key for key, value in data.items() if key in columns and value is None and not columns[key].nullable]
        if invalid_nulls:
            db.session.rollback()
            return jsonify({"error": "Estos campos no pueden ser null", "fields": invalid_nulls}), 422
        for key, value in data.items():
            if key in columns:
                setattr(item, key, value)
        db.session.commit()
        return jsonify(serialize_model(item, ("contraseña",)))

    @blueprint.delete("/<int:identifier>")
    @roles_required(*write_roles)
    def delete_item(identifier):
        db.session.delete(service.get_record(identifier))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "No se puede eliminar el recurso porque tiene registros relacionados"}), 409
        return "", 204

    return blueprint
