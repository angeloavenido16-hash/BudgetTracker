"""add_is_active_to_expense_categories — soft-delete support.

Revision ID: 8d5a2c65d5e3
Revises: 0001_initial
Create Date: 2026-06-29 22:22:28.061894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8d5a2c65d5e3'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'expense_categories',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )


def downgrade() -> None:
    op.drop_column('expense_categories', 'is_active')
