"""bot-actions-foundation-phase-1

Revision ID: 138_bot_actions_foundation
Revises: 791923be29e5
Create Date: 2026-05-06 02:45:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "138_bot_actions_foundation"
down_revision: Union[str, None] = "791923be29e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


http_method_enum = sa.Enum("GET", "POST", "PUT", "PATCH", "DELETE", name="http_method_enum")


def upgrade() -> None:
    bind = op.get_bind()
    http_method_enum.create(bind, checkfirst=True)

    op.create_table(
        "bot_actions",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("trigger_prompt", sa.Text(), nullable=True),
        sa.Column("ai_instructions", sa.Text(), nullable=True),
        sa.Column("method", http_method_enum, nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("headers_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("query_params_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("body_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("variables_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("auth_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_config_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("timeout_ms", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bot_actions_tenant_id", "bot_actions", ["tenant_id"])
    op.create_index("ix_bot_actions_enabled", "bot_actions", ["enabled"])

    op.create_table(
        "channel_bot_action_links",
        sa.Column("channel_bot_config_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bot_action_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bot_action_id"], ["bot_actions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["channel_bot_config_id"], ["channel_bot_configs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_bot_config_id", "bot_action_id", name="uq_channel_bot_action_link"),
    )
    op.create_index(
        "ix_channel_bot_action_links_channel_bot_config_id",
        "channel_bot_action_links",
        ["channel_bot_config_id"],
    )
    op.create_index("ix_channel_bot_action_links_bot_action_id", "channel_bot_action_links", ["bot_action_id"])

    op.create_table(
        "bot_action_executions",
        sa.Column("bot_action_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bot_action_id"], ["bot_actions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bot_action_executions_bot_action_id", "bot_action_executions", ["bot_action_id"])
    op.create_index("ix_bot_action_executions_channel_id", "bot_action_executions", ["channel_id"])
    op.create_index("ix_bot_action_executions_conversation_id", "bot_action_executions", ["conversation_id"])
    op.create_index("ix_bot_action_executions_created_at", "bot_action_executions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_bot_action_executions_created_at", table_name="bot_action_executions")
    op.drop_index("ix_bot_action_executions_conversation_id", table_name="bot_action_executions")
    op.drop_index("ix_bot_action_executions_channel_id", table_name="bot_action_executions")
    op.drop_index("ix_bot_action_executions_bot_action_id", table_name="bot_action_executions")
    op.drop_table("bot_action_executions")

    op.drop_index("ix_channel_bot_action_links_bot_action_id", table_name="channel_bot_action_links")
    op.drop_index(
        "ix_channel_bot_action_links_channel_bot_config_id",
        table_name="channel_bot_action_links",
    )
    op.drop_table("channel_bot_action_links")

    op.drop_index("ix_bot_actions_enabled", table_name="bot_actions")
    op.drop_index("ix_bot_actions_tenant_id", table_name="bot_actions")
    op.drop_table("bot_actions")

    http_method_enum.drop(op.get_bind(), checkfirst=True)
