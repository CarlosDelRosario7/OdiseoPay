from ..models import DetalleVenta
from ..services import detalle_venta_service as service
from .base_routes import crud_blueprint

service.list_records = service.list_sale_details
service.get_record = service.get_sale_detail
detalle_venta_blueprint = crud_blueprint("detalle_ventas", "/api/detalle-ventas", DetalleVenta, service, ("Admin", "Vendedor"))
