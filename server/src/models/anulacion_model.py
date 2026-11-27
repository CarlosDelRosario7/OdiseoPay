from ..extensions import db


class Anulacion(db.Model):
    """Registro de auditoría de una operación anulada, con fecha UTC."""

    __tablename__ = "anulaciones"
    __table_args__ = (
        db.UniqueConstraint("tipo_operacion", "id_operacion", name="uq_anulacion_operacion"),
        db.CheckConstraint("tipo_operacion IN ('VENTA', 'COMPRA')", name="ck_anulacion_tipo"),
    )

    id_anulacion = db.Column(db.Integer, primary_key=True)
    tipo_operacion = db.Column(db.String(10), nullable=False)
    id_operacion = db.Column(db.Integer, nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"), nullable=False)
    fecha_utc = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(255), nullable=False)
    usuario = db.relationship("Usuario")
