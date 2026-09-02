from ..models import Producto
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_products(page, per_page): return paginate_records(Producto, page, per_page)
def get_product(identifier): return get_or_404(Producto, identifier)
def delete_product(instance): return delete_record(instance)
