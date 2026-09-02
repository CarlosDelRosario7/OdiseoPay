from ..extensions import db


class Producto(db.Model):
    __tablename__ = "productos"
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(255))
    precio_compra = db.Column(db.Numeric(10, 2), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey("categorias.id_categoria"), nullable=False)
    id_proveedor = db.Column(db.Integer, db.ForeignKey("proveedores.id_proveedor"), nullable=False)
    categoria = db.relationship("Categoria", back_populates="productos")
    proveedor = db.relationship("Proveedor", back_populates="productos")
    inventario = db.relationship("Inventario", back_populates="producto", uselist=False)
    detalles_compra = db.relationship("DetalleCompra", back_populates="producto")
    detalles_venta = db.relationship("DetalleVenta", back_populates="producto")
    movimientos = db.relationship("MovimientoInventario", back_populates="producto")
