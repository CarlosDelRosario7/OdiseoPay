from ..extensions import db


class Cliente(db.Model):
    __tablename__ = "clientes"
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(150), unique=True)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(255))
    ventas = db.relationship("Venta", back_populates="cliente")
