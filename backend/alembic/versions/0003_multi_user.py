"""multi_user_support — add users table and user_id to all data tables.

Database-agnostic rewrite: uses Alembic batch_alter_table so it works on
both SQLite (which requires table recreation) and Postgres (ALTER TABLE).

Revision ID: 0003
Revises: 8d5a2c65d5e3
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "8d5a2c65d5e3"


def upgrade() -> None:
    # ── users table ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.execute(
        "INSERT INTO users (username, password_hash) "
        "VALUES ('admin', 'placeholder')"
    )

    # ── funds: add user_id, switch from UNIQUE(name) to UNIQUE(user_id, name)
    with op.batch_alter_table("funds", recreate="auto") as bop:
        bop.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
                server_default=sa.text("1"),
            )
        )
        bop.drop_constraint("uq_funds_name", type_="unique")
        bop.create_unique_constraint(
            "uq_funds_user_name", ["user_id", "name"]
        )

    # ── expense_categories: same pattern
    with op.batch_alter_table("expense_categories", recreate="auto") as bop:
        bop.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
                server_default=sa.text("1"),
            )
        )
        bop.drop_constraint(
            "uq_expense_categories_name", type_="unique"
        )
        bop.create_unique_constraint(
            "uq_expense_categories_user_name", ["user_id", "name"]
        )

    # ── transactions: add user_id
    with op.batch_alter_table("transactions", recreate="auto") as bop:
        bop.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
                server_default=sa.text("1"),
            )
        )

    # ── bpi_balance: add user_id
    with op.batch_alter_table("bpi_balance", recreate="auto") as bop:
        bop.add_column(
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
                server_default=sa.text("1"),
            )
        )


def downgrade() -> None:
    # Reverse order to avoid FK issues.
    # Drop user_id first on the FK-referencing tables; the composite
    # UNIQUE constraint that references it disappears with the column.
    with op.batch_alter_table("bpi_balance", recreate="auto") as bop:
        bop.drop_column("user_id")

    with op.batch_alter_table("transactions", recreate="auto") as bop:
        bop.drop_column("user_id")

    # Recreate without user_id and restore UNIQUE(name).
    with op.batch_alter_table("expense_categories", recreate="always") as bop:
        bop.drop_column("user_id")
        bop.create_unique_constraint(
            "uq_expense_categories_name", ["name"]
        )

    with op.batch_alter_table("funds", recreate="always") as bop:
        bop.drop_column("user_id")
        bop.create_unique_constraint("uq_funds_name", ["name"])

    op.execute("DELETE FROM users WHERE username = 'admin'")
    op.drop_table("users")
