from ..models import DetalleCompra
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_purchase_details(page, per_page): return paginate_records(DetalleCompra, page, per_page)
def get_purchase_detail(identifier): return get_or_404(DetalleCompra, identifier)
def delete_purchase_detail(instance): return delete_record(instance)
