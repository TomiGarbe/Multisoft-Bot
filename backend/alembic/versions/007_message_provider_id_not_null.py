"""Enforce non-null provider_message_id on messages

Revision ID: 007_message_provider_id_not_null
Revises: 006_drop_tenant_bot_configs
Create Date: 2026-04-30 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "007_message_provider_id_not_null"
down_revision: Union[str, None] = "006_drop_tenant_bot_configs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE messages
        SET provider_message_id = id::text
        WHERE provider_message_id IS NULL
    """)
    op.alter_column("messages", "provider_message_id", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    op.alter_column("messages", "provider_message_id", existing_type=sa.String(length=255), nullable=True)
