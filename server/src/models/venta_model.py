from ..extensions import db


class Venta(db.Model):
    __tablename__ = "ventas"
    id_venta = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    id_cliente = db.Column(db.Integer, db.ForeignKey("clientes.id_cliente"), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"), nullable=False)
    cliente = db.relationship("Cliente", back_populates="ventas")
    usuario = db.relationship("Usuario", back_populates="ventas")
    detalles = db.relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")
