"""Add user_types_jsonb and settings_jsonb to channel_bot_configs; add current_type to users

Revision ID: 003_user_types
Revises: 002_add_ai_logs
Create Date: 2026-04-27 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = '003_user_types'
down_revision: Union[str, None] = '002_add_ai_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('channel_bot_configs', sa.Column('user_types_jsonb', JSONB(), nullable=True))
    op.add_column('channel_bot_configs', sa.Column('settings_jsonb', JSONB(), nullable=True))
    op.add_column('users', sa.Column('current_type', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'current_type')
    op.drop_column('channel_bot_configs', 'settings_jsonb')
    op.drop_column('channel_bot_configs', 'user_types_jsonb')
