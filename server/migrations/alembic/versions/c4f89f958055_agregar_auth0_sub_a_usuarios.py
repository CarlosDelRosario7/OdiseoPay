"""Agregar auth0_sub a usuarios

Revision ID: c4f89f958055
Revises: 
Create Date: 2026-09-28 13:56:41.483634
"""
from alembic import op
import sqlalchemy as sa


revision = 'c4f89f958055'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuarios",
        sa.Column("auth0_sub", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_usuarios_auth0_sub",
        "usuarios",
        ["auth0_sub"],
    )


def downgrade():
    op.drop_constraint(
        "uq_usuarios_auth0_sub",
        "usuarios",
        type_="unique",
    )
    op.drop_column("usuarios", "auth0_sub")
