from ..extensions import db


class Proveedor(db.Model):
    __tablename__ = "proveedores"
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(150))
    direccion = db.Column(db.String(255))
    productos = db.relationship("Producto", back_populates="proveedor")
    compras = db.relationship("Compra", back_populates="proveedor")
