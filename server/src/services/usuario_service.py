from ..extensions import db
from ..models import Usuario
from ..utils.auth_utils import hash_password
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_users(page, per_page): return paginate_records(Usuario, page, per_page)
def get_user(identifier): return get_or_404(Usuario, identifier)
def delete_user(instance): return delete_record(instance)


def create_user(data):
    user = Usuario(nombre=data["nombre"], usuario=data["usuario"], rol=data["rol"], contrasena=hash_password(data["contrasena"]))
    db.session.add(user)
    db.session.commit()
    return user
