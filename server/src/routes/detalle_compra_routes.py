from ..models import DetalleCompra
from ..services import detalle_compra_service as service
from .base_routes import crud_blueprint

service.list_records = service.list_purchase_details
service.get_record = service.get_purchase_detail
detalle_compra_blueprint = crud_blueprint("detalle_compras", "/api/detalle-compras", DetalleCompra, service, read_roles=("Admin",))
