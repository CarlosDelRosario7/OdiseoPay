from ..models import Proveedor
from ..services import proveedor_service as service
from .base_routes import crud_blueprint

service.list_records = service.list_providers
service.get_record = service.get_provider
proveedor_blueprint = crud_blueprint("proveedores", "/api/proveedores", Proveedor, service, read_roles=("Admin",))
