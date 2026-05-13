"""142_media_processing_foundation

Revision ID: 8d2f5b53f6d1
Revises: e11c90f95b01
Create Date: 2026-05-13 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8d2f5b53f6d1"
down_revision: Union[str, None] = "e11c90f95b01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attachment_processing_jobs",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("attachment_id", sa.UUID(), nullable=False),
        sa.Column("capability", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["attachment_id"], ["message_attachments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attachment_processing_jobs_attachment_id", "attachment_processing_jobs", ["attachment_id"])
    op.create_index(
        "ix_attachment_processing_jobs_tenant_status", "attachment_processing_jobs", ["tenant_id", "status"]
    )
    op.create_index("ix_attachment_processing_jobs_capability", "attachment_processing_jobs", ["capability"])

    op.create_table(
        "processed_artifacts",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("attachment_id", sa.UUID(), nullable=False),
        sa.Column("capability", sa.String(length=40), nullable=False),
        sa.Column("storage_backend", sa.String(length=20), nullable=False, server_default="inline_json"),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("payload_text", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=150), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["attachment_id"], ["message_attachments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processed_artifacts_attachment_id", "processed_artifacts", ["attachment_id"])
    op.create_index("ix_processed_artifacts_tenant_capability", "processed_artifacts", ["tenant_id", "capability"])

    op.alter_column("attachment_processing_jobs", "status", server_default=None)
    op.alter_column("attachment_processing_jobs", "retry_count", server_default=None)
    op.alter_column("attachment_processing_jobs", "max_attempts", server_default=None)
    op.alter_column("processed_artifacts", "storage_backend", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_processed_artifacts_tenant_capability", table_name="processed_artifacts")
    op.drop_index("ix_processed_artifacts_attachment_id", table_name="processed_artifacts")
    op.drop_table("processed_artifacts")

    op.drop_index("ix_attachment_processing_jobs_capability", table_name="attachment_processing_jobs")
    op.drop_index("ix_attachment_processing_jobs_tenant_status", table_name="attachment_processing_jobs")
    op.drop_index("ix_attachment_processing_jobs_attachment_id", table_name="attachment_processing_jobs")
    op.drop_table("attachment_processing_jobs")
