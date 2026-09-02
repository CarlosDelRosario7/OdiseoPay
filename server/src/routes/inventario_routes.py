from ..models import Inventario
from ..services import inventario_service as service
from .base_routes import crud_blueprint

service.list_records = service.list_inventory
service.get_record = service.get_inventory
inventario_blueprint = crud_blueprint("inventario", "/api/inventario", Inventario, service)
