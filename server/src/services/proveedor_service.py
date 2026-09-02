from ..models import Proveedor
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_providers(page, per_page): return paginate_records(Proveedor, page, per_page)
def get_provider(identifier): return get_or_404(Proveedor, identifier)
def delete_provider(instance): return delete_record(instance)
