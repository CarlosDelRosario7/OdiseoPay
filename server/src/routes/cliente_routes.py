from ..models import Cliente
from ..services import cliente_service as service
from .base_routes import crud_blueprint

service.list_records = service.list_clients
service.get_record = service.get_client
cliente_blueprint = crud_blueprint("clientes", "/api/clientes", Cliente, service, read_roles=("Admin",))
