from ..models import MovimientoInventario
from .base_service import get_or_404, list_records as paginate_records


def list_inventory_movements(page, per_page): return paginate_records(MovimientoInventario, page, per_page)
def get_inventory_movement(identifier): return get_or_404(MovimientoInventario, identifier)
