from ..models import MovimientoInventario
from ..services import movimiento_inventario_service as service
from .base_routes import crud_blueprint

service.list_records = service.list_inventory_movements
service.get_record = service.get_inventory_movement
movimiento_blueprint = crud_blueprint("movimientos", "/api/movimientos-inventario", MovimientoInventario, service, read_roles=("Admin",))
