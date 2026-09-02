from ..models import DetalleVenta
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_sale_details(page, per_page): return paginate_records(DetalleVenta, page, per_page)
def get_sale_detail(identifier): return get_or_404(DetalleVenta, identifier)
def delete_sale_detail(instance): return delete_record(instance)
