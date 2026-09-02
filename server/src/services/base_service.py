from flask import abort

from ..extensions import db


def get_or_404(model, identifier):
    instance = db.session.get(model, identifier)
    if instance is None:
        abort(404, description="Recurso no encontrado")
    return instance


def list_records(model, page=1, per_page=20):
    return db.paginate(db.select(model), page=page, per_page=min(per_page, 100), error_out=False)


def delete_record(instance):
    db.session.delete(instance)
    db.session.commit()
