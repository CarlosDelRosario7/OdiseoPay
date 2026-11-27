"""Registrar anulaciones de ventas y compras.

Revision ID: f4a7219e4a01
Revises: c4f89f958055
"""

from alembic import op
import sqlalchemy as sa

revision = "f4a7219e4a01"
down_revision = "c4f89f958055"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "anulaciones",
        sa.Column("id_anulacion", sa.Integer(), primary_key=True),
        sa.Column("tipo_operacion", sa.String(10), nullable=False),
        sa.Column("id_operacion", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("usuarios.id_usuario"), nullable=False),
        sa.Column("fecha_utc", sa.DateTime(), nullable=False),
        sa.Column("motivo", sa.String(255), nullable=False),
        sa.UniqueConstraint("tipo_operacion", "id_operacion", name="uq_anulacion_operacion"),
        sa.CheckConstraint("tipo_operacion IN ('VENTA', 'COMPRA')", name="ck_anulacion_tipo"),
    )


def downgrade():
    op.drop_table("anulaciones")
