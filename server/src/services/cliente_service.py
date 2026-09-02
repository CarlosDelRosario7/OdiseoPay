from ..models import Cliente
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_clients(page, per_page): return paginate_records(Cliente, page, per_page)
def get_client(identifier): return get_or_404(Cliente, identifier)
def delete_client(instance): return delete_record(instance)
