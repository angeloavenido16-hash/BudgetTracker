"""initial schema — funds, transactions, expense_categories, bpi_balance

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-29

Mirrors the desktop app's 4-table SQLite schema (see ../../../database.py) so
the data-port script (migrate_sqlite_to_postgres.py) lands cleanly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── expense_categories ──────────────────────────────────────────────────
    op.create_table(
        "expense_categories",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_expense_categories"),
        sa.UniqueConstraint("name", name="uq_expense_categories_name"),
    )

    # ── funds ───────────────────────────────────────────────────────────────
    op.create_table(
        "funds",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("fund_type", sa.String(), nullable=False, server_default="salary"),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cutoff_date", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_funds"),
        sa.UniqueConstraint("name", name="uq_funds_name"),
    )

    # ── transactions ────────────────────────────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("fund_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("txn_date", sa.String(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_transactions"),
        sa.ForeignKeyConstraint(
            ["fund_id"], ["funds.id"],
            name="fk_transactions_fund_id_funds",
            ondelete="CASCADE",
        ),
    )
    # Helpful index — most reads filter transactions by fund.
    op.create_index(
        "ix_transactions_fund_id", "transactions", ["fund_id"],
    )

    # ── bpi_balance ─────────────────────────────────────────────────────────
    op.create_table(
        "bpi_balance",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("balance", sa.Float(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bpi_balance"),
    )


def downgrade() -> None:
    op.drop_table("bpi_balance")
    op.drop_index("ix_transactions_fund_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("funds")
    op.drop_table("expense_categories")
