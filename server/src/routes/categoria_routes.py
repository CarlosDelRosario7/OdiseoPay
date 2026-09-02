from ..models import Categoria
from ..services import categoria_service as service
from .base_routes import crud_blueprint

service.list_records = service.list_categories
service.get_record = service.get_category
categoria_blueprint = crud_blueprint("categorias", "/api/categorias", Categoria, service)
