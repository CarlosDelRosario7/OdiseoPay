from ..extensions import db


class MovimientoInventario(db.Model):
    __tablename__ = "movimientos_inventario"
    id_movimiento = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey("productos.id_producto"), nullable=False)
    tipo = db.Column(db.Enum("ENTRADA", "SALIDA", "AJUSTE"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    motivo = db.Column(db.String(255))
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"), nullable=False)
    producto = db.relationship("Producto", back_populates="movimientos")
    usuario = db.relationship("Usuario", back_populates="movimientos")
