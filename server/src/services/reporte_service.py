from ..extensions import db
from ..models import Inventario, Producto


def bajo_stock(umbral=None, page=1, per_page=20):
    """Lista los productos cuyo stock esta por debajo del umbral indicado.

    Si no se indica un umbral, se usa el stock_minimo propio de cada producto.
    Si se indica, se compara contra ese valor fijo (ajustable desde el software).
    """
    limite = umbral if umbral is not None else Inventario.stock_minimo
    query = (
        db.select(Inventario)
        .join(Producto, Inventario.id_producto == Producto.id_producto)
        .where(Inventario.cantidad < limite)
        .order_by(Inventario.cantidad.asc())
    )
    pagination = db.paginate(query, page=page, per_page=min(per_page, 100), error_out=False)
    return pagination


def resumen_bajo_stock(umbral=None):
    """Cuenta cuantos productos estan en bajo stock segun el umbral efectivo."""
    limite = umbral if umbral is not None else Inventario.stock_minimo
    total = db.session.scalar(
        db.select(db.func.count()).select_from(Inventario).where(Inventario.cantidad < limite)
    )
    return int(total or 0)


def actualizar_stock_minimo(id_producto, stock_minimo):
    """Actualiza el stock minimo (umbral) de un producto concreto."""
    inventario = db.session.scalar(
        db.select(Inventario).where(Inventario.id_producto == id_producto)
    )
    if inventario is None:
        return None
    inventario.stock_minimo = stock_minimo
    db.session.commit()
    return inventario
