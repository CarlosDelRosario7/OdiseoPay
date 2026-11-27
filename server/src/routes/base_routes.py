from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Anulacion, MovimientoInventario
from ..services.anulacion_service import serializar as serializar_anulacion
from ..utils.auth_utils import current_user_id, hash_password, roles_required
from ..utils.serialization_utils import serialize_model


def crud_blueprint(name, url_prefix, model, service, write_roles=("Admin",), read_roles=("Admin", "Vendedor"), include_create=True):
    blueprint = Blueprint(name, __name__, url_prefix=url_prefix)

    def serialize_items(items):
        if name not in {"ventas", "compras"}:
            return [serialize_model(item, ("contraseña",)) for item in items]
        tipo = "VENTA" if name == "ventas" else "COMPRA"
        id_field = "id_venta" if name == "ventas" else "id_compra"
        ids = [getattr(item, id_field) for item in items]
        registros = db.session.scalars(
            db.select(Anulacion).where(
                Anulacion.tipo_operacion == tipo, Anulacion.id_operacion.in_(ids)
            )
        ).all() if ids else []
        por_id = {registro.id_operacion: registro for registro in registros}
        result = []
        for item in items:
            data = serialize_model(item, ("contraseña",))
            registro = por_id.get(getattr(item, id_field))
            data["estado"] = "ANULADA" if registro else "ACTIVA"
            data["anulacion"] = serializar_anulacion(registro) if registro else None
            result.append(data)
        return result

    @blueprint.get("")
    @roles_required(*read_roles)
    def list_items():
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        pagination = service.list_records(page, per_page)
        return jsonify({"items": serialize_items(pagination.items), "page": pagination.page, "per_page": pagination.per_page, "total": pagination.total, "pages": pagination.pages})

    @blueprint.get("/<int:identifier>")
    @roles_required(*read_roles)
    def get_item(identifier):
        return jsonify(serialize_items([service.get_record(identifier)])[0])

    if include_create:
        @blueprint.post("")
        @roles_required(*write_roles)
        def create_item():
            if name in {"detalle_ventas", "detalle_compras"}:
                return jsonify({"error": "Los detalles se crean junto con la operación"}), 405
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
        if name in {"ventas", "compras", "detalle_ventas", "detalle_compras"}:
            return jsonify({"error": "Esta operación no admite modificaciones directas"}), 405
        item = service.get_record(identifier)
        data = request.get_json(silent=True) or {}
        if name == "usuarios" and "rol" in data and data["rol"] not in {"Admin", "Vendedor"}:
            return jsonify({"error": "El rol debe ser Admin o Vendedor"}), 422
        if name == "inventario":
            for field in ("cantidad", "stock_minimo"):
                if field in data and (not isinstance(data[field], int) or isinstance(data[field], bool) or data[field] < 0):
                    return jsonify({"error": f"{field} debe ser un entero mayor o igual a 0"}), 422
            if "cantidad" in data:
                db.session.refresh(item, with_for_update=True)
                previous = item.cantidad
                delta = data["cantidad"] - previous
                if delta:
                    db.session.add(MovimientoInventario(
                        id_producto=item.id_producto, tipo="AJUSTE", cantidad=delta,
                        motivo=f"Ajuste de {previous} a {data['cantidad']}",
                        id_usuario=current_user_id(),
                    ))
        columns = {column.name: column for column in model.__table__.columns if not column.primary_key}
        invalid_nulls = [key for key, value in data.items() if key in columns and value is None and not columns[key].nullable]
        if invalid_nulls:
            db.session.rollback()
            return jsonify({"error": "Estos campos no pueden ser null", "fields": invalid_nulls}), 422
        for key, value in data.items():
            # Aceptar ambas grafías sin permitir almacenar texto plano.
            if name == "usuarios" and key in ("contrasena", "contraseña"):
                if value:
                    item.contrasena = hash_password(value)
            elif key in columns:
                setattr(item, key, value)
        db.session.commit()
        return jsonify(serialize_model(item, ("contraseña",)))

    @blueprint.delete("/<int:identifier>")
    @roles_required(*write_roles)
    def delete_item(identifier):
        if name in {"ventas", "compras", "detalle_ventas", "detalle_compras"}:
            return jsonify({"error": "Esta operación no admite eliminación directa"}), 405
        db.session.delete(service.get_record(identifier))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "No se puede eliminar el recurso porque tiene registros relacionados"}), 409
        return "", 204

    return blueprint
