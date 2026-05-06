"""ai-usage-events-refactor

Revision ID: 137_ai_usage_events_refactor
Revises: 136_api_keys_foundation
Create Date: 2026-05-06 00:10:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "137_ai_usage_events_refactor"
down_revision: Union[str, None] = "136_api_keys_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("contact_usage_daily")
    op.drop_table("usage_daily")
    op.drop_table("token_usage")

    op.create_table(
        "ai_usage_events",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.BigInteger(), nullable=False),
        sa.Column("output_tokens", sa.BigInteger(), nullable=False),
        sa.Column("total_tokens", sa.BigInteger(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_events_tenant_id", "ai_usage_events", ["tenant_id"])
    op.create_index("ix_ai_usage_events_channel_id", "ai_usage_events", ["channel_id"])
    op.create_index("ix_ai_usage_events_conversation_id", "ai_usage_events", ["conversation_id"])
    op.create_index("ix_ai_usage_events_created_at", "ai_usage_events", ["created_at"])
    op.create_index("ix_ai_usage_events_request_id", "ai_usage_events", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_events_request_id", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_created_at", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_conversation_id", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_channel_id", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_tenant_id", table_name="ai_usage_events")
    op.drop_table("ai_usage_events")

    op.create_table(
        "token_usage",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt_tokens", sa.BigInteger(), nullable=False),
        sa.Column("completion_tokens", sa.BigInteger(), nullable=False),
        sa.Column("total_tokens", sa.BigInteger(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_token_usage_tenant_id", "token_usage", ["tenant_id"])
    op.create_index("ix_token_usage_created_at", "token_usage", ["created_at"])

    op.create_table(
        "usage_daily",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("tokens_used", sa.BigInteger(), nullable=False),
        sa.Column("messages_inbound", sa.Integer(), nullable=False),
        sa.Column("messages_outbound", sa.Integer(), nullable=False),
        sa.Column("contacts_active", sa.Integer(), nullable=False),
        sa.Column("conversations_started", sa.Integer(), nullable=False),
        sa.Column("ai_requests", sa.Integer(), nullable=False),
        sa.Column("actions_executed", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "date", name="uq_usage_daily_tenant_date"),
    )

    op.create_table(
        "contact_usage_daily",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("tokens_used", sa.BigInteger(), nullable=False),
        sa.Column("messages_inbound", sa.Integer(), nullable=False),
        sa.Column("messages_outbound", sa.Integer(), nullable=False),
        sa.Column("ai_requests", sa.Integer(), nullable=False),
        sa.Column("conversations_started", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contact_id", "date", name="uq_contact_usage_daily_contact_date"),
    )
