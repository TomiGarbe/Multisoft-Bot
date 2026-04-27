"""Add ai_logs table for AI interaction logging

Revision ID: 002_add_ai_logs
Revises: 001_refactor_bot_config
Create Date: 2026-04-27 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = '002_add_ai_logs'
down_revision: Union[str, None] = '001_refactor_bot_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel_id', UUID(as_uuid=True), sa.ForeignKey('channels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', UUID(as_uuid=True), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_ai_logs_tenant_id', 'ai_logs', ['tenant_id'])
    op.create_index('ix_ai_logs_channel_id', 'ai_logs', ['channel_id'])
    op.create_index('ix_ai_logs_conversation_id', 'ai_logs', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_ai_logs_conversation_id', table_name='ai_logs')
    op.drop_index('ix_ai_logs_channel_id', table_name='ai_logs')
    op.drop_index('ix_ai_logs_tenant_id', table_name='ai_logs')
    op.drop_table('ai_logs')
