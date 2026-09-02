from ..extensions import db


class Compra(db.Model):
    __tablename__ = "compras"
    id_compra = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    id_proveedor = db.Column(db.Integer, db.ForeignKey("proveedores.id_proveedor"), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"), nullable=False)
    proveedor = db.relationship("Proveedor", back_populates="compras")
    usuario = db.relationship("Usuario", back_populates="compras")
    detalles = db.relationship("DetalleCompra", back_populates="compra", cascade="all, delete-orphan")
