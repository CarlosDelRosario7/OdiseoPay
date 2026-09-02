from ..extensions import db


class DetalleCompra(db.Model):
    __tablename__ = "detalle_compra"
    id_detalle_compra = db.Column(db.Integer, primary_key=True)
    id_compra = db.Column(db.Integer, db.ForeignKey("compras.id_compra"), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey("productos.id_producto"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    compra = db.relationship("Compra", back_populates="detalles")
    producto = db.relationship("Producto", back_populates="detalles_compra")
