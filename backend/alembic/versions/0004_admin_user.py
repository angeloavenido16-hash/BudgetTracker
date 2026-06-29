"""add is_admin and is_active to users table.

Revision ID: 0004
Revises: 0003
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"


def upgrade() -> None:
    with op.batch_alter_table("users") as bop:
        bop.add_column(
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )
        bop.add_column(
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true"))
        )

    # Mark the initial admin user as admin
    op.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")


def downgrade() -> None:
    with op.batch_alter_table("users") as bop:
        bop.drop_column("is_active")
        bop.drop_column("is_admin")
