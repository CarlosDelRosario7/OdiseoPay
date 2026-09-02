from ..models import Producto
from ..services import producto_service as service
from .base_routes import crud_blueprint

service.list_records = service.list_products
service.get_record = service.get_product
producto_blueprint = crud_blueprint("productos", "/api/productos", Producto, service)
