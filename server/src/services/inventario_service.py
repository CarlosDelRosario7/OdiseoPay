from ..models import Inventario
from .base_service import get_or_404, list_records as paginate_records


def list_inventory(page, per_page): return paginate_records(Inventario, page, per_page)
def get_inventory(identifier): return get_or_404(Inventario, identifier)
