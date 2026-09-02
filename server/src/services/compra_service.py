from decimal import Decimal

from ..extensions import db
from ..models import Compra, DetalleCompra, Inventario, MovimientoInventario, Producto
from .base_service import delete_record, get_or_404, list_records as paginate_records


def list_purchases(page, per_page): return paginate_records(Compra, page, per_page)
def get_purchase(identifier): return get_or_404(Compra, identifier)
def delete_purchase(instance): return delete_record(instance)


def create_purchase(data, user_id):
	details = data.get("detalles", [])
	if not details or not data.get("id_proveedor"):
		raise ValueError("Una compra requiere proveedor y al menos un detalle")
	purchase = Compra(id_proveedor=data["id_proveedor"], id_usuario=user_id)
	db.session.add(purchase)
	for detail in details:
		quantity = int(detail["cantidad"])
		price = Decimal(str(detail["precio"]))
		if quantity <= 0 or price < 0:
			raise ValueError("Cantidad y precio deben ser válidos")
		product = db.session.get(Producto, detail["id_producto"])
		if product is None:
			raise ValueError("Producto inexistente")
		purchase.detalles.append(DetalleCompra(id_producto=product.id_producto, cantidad=quantity, precio=price))
		inventory = product.inventario or Inventario(id_producto=product.id_producto, cantidad=0)
		inventory.cantidad += quantity
		db.session.add(inventory)
		db.session.add(MovimientoInventario(id_producto=product.id_producto, tipo="ENTRADA", cantidad=quantity, motivo="Compra", id_usuario=user_id))
	db.session.commit()
	return purchase
