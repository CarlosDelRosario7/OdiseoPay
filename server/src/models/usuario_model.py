from ..extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), nullable=False, unique=True)
    contrasena = db.Column("contraseña", db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False)
    auth0_sub = db.Column(db.String(255), nullable=True, unique=True)
    compras = db.relationship("Compra", back_populates="usuario")
    ventas = db.relationship("Venta", back_populates="usuario")
    movimientos = db.relationship("MovimientoInventario", back_populates="usuario")
