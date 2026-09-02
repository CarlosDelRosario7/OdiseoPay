from ..models import Categoria
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_categories(page, per_page): return paginate_records(Categoria, page, per_page)
def get_category(identifier): return get_or_404(Categoria, identifier)
def delete_category(instance): return delete_record(instance)
