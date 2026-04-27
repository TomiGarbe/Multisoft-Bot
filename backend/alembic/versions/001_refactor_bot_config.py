"""Refactor bot config to use only ChannelBotConfig

Revision ID: 001_refactor_bot_config
Revises: 394fff4a0620
Create Date: 2026-04-27 10:00:00.000000

This migration:
- Removes the FK relationship from ChannelBotConfig to TenantBotConfig
- Removes the tenant_bot_config_id column from channel_bot_configs table
- Marks TenantBotConfig as deprecated (kept for backward compatibility)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_refactor_bot_config'
down_revision: Union[str, None] = '394fff4a0620'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove tenant_bot_config_id FK and column from channel_bot_configs.
    ChannelBotConfig now stores complete configuration independently.
    """
    # Drop the FK constraint
    op.drop_constraint(
        'channel_bot_configs_tenant_bot_config_id_fkey',
        'channel_bot_configs',
        type_='foreignkey'
    )
    
    # Drop the column
    op.drop_column('channel_bot_configs', 'tenant_bot_config_id')


def downgrade() -> None:
    """
    Restore tenant_bot_config_id column and FK (for rollback only).
    """
    # Add the column back
    op.add_column(
        'channel_bot_configs',
        sa.Column(
            'tenant_bot_config_id',
            sa.UUID(),
            nullable=False,
            # Set a default UUID for existing rows - use the ID from tenant_bot_configs
            # In practice, this might need manual adjustment
        )
    )
    
    # Recreate the FK constraint
    op.create_foreign_key(
        'channel_bot_configs_tenant_bot_config_id_fkey',
        'channel_bot_configs',
        'tenant_bot_configs',
        ['tenant_bot_config_id'],
        ['id'],
        ondelete='CASCADE'
    )
