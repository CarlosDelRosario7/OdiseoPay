from ..extensions import db


class Inventario(db.Model):
    __tablename__ = "inventario"
    id_inventario = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey("productos.id_producto"), nullable=False, unique=True)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)
    ubicacion = db.Column(db.String(100))
    producto = db.relationship("Producto", back_populates="inventario")
