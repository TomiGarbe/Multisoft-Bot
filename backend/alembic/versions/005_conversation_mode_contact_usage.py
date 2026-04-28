"""Add conversation.mode and contact_usage table

Revision ID: 005_conversation_mode_contact_usage
Revises: 004_contact_current_type
Create Date: 2026-04-27 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = '005_conversation_mode_contact_usage'
down_revision: Union[str, None] = '004_contact_current_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add mode column to conversations ("ai" | "human")
    op.add_column(
        'conversations',
        sa.Column('mode', sa.String(10), nullable=False, server_default='ai'),
    )

    # Create contact_usage table (1 record per active conversation)
    op.create_table(
        'contact_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'contact_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('contacts.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'conversation_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('conversations.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('bot_message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint('conversation_id', name='uq_contact_usage_conversation'),
    )
    op.create_index('ix_contact_usage_contact_id', 'contact_usage', ['contact_id'])
    op.create_index('ix_contact_usage_conversation_id', 'contact_usage', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_contact_usage_conversation_id', table_name='contact_usage')
    op.drop_index('ix_contact_usage_contact_id', table_name='contact_usage')
    op.drop_table('contact_usage')
    op.drop_column('conversations', 'mode')
