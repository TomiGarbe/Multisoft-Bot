"""Add token_usage table for per-request AI token tracking

Revision ID: 008_add_token_usage
Revises: 007_message_provider_id_not_null
Create Date: 2026-05-04 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "008_add_token_usage"
down_revision: Union[str, None] = "007_message_provider_id_not_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index("ix_token_usage_created_at", table_name="token_usage")
    op.drop_index("ix_token_usage_tenant_id", table_name="token_usage")
    op.drop_table("token_usage")
