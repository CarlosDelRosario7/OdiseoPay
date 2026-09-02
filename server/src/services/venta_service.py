from decimal import Decimal

from ..extensions import db
from ..models import DetalleVenta, Inventario, MovimientoInventario, Producto, Venta
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_sales(page, per_page): return paginate_records(Venta, page, per_page)
def get_sale(identifier): return get_or_404(Venta, identifier)
def delete_sale(instance): return delete_record(instance)


def create_sale(data, user_id):
	details = data.get("detalles", [])
	if not details or not data.get("id_cliente"):
		raise ValueError("Una venta requiere cliente y al menos un detalle")
	sale = Venta(id_cliente=data["id_cliente"], id_usuario=user_id)
	db.session.add(sale)
	for detail in details:
		quantity = int(detail["cantidad"])
		price = Decimal(str(detail["precio"]))
		product = db.session.get(Producto, detail["id_producto"])
		inventory = product.inventario if product else None
		if product is None or inventory is None or quantity <= 0 or price < 0:
			raise ValueError("Producto, cantidad, precio o inventario inválidos")
		if inventory.cantidad < quantity:
			raise ValueError("Stock insuficiente")
		sale.detalles.append(DetalleVenta(id_producto=product.id_producto, cantidad=quantity, precio=price))
		inventory.cantidad -= quantity
		db.session.add(MovimientoInventario(id_producto=product.id_producto, tipo="SALIDA", cantidad=quantity, motivo="Venta", id_usuario=user_id))
	db.session.commit()
	return sale
