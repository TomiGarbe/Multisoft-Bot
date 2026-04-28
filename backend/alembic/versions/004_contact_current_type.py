"""Move current_type from users to contacts

Revision ID: 004_contact_current_type
Revises: 003_user_types
Create Date: 2026-04-27 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '004_contact_current_type'
down_revision: Union[str, None] = '003_user_types'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contacts', sa.Column('current_type', sa.String(50), nullable=True))
    op.drop_column('users', 'current_type')


def downgrade() -> None:
    op.add_column('users', sa.Column('current_type', sa.String(50), nullable=True))
    op.drop_column('contacts', 'current_type')
