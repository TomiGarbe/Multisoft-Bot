"""141_attachments_metadata_blobs_refactor

Revision ID: e11c90f95b01
Revises: 140_user_type_labels
Create Date: 2026-05-13 14:12:49.173737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision: str = 'e11c90f95b01'
down_revision: Union[str, None] = '140_user_type_labels'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "message_attachments",
        sa.Column("storage_backend", sa.String(length=20), nullable=False, server_default="none"),
    )
    op.add_column("message_attachments", sa.Column("storage_key", sa.String(length=512), nullable=True))
    op.add_column("message_attachments", sa.Column("provider_media_id", sa.String(length=255), nullable=True))
    op.add_column("message_attachments", sa.Column("provider_url", sa.String(length=2048), nullable=True))
    op.add_column("message_attachments", sa.Column("filename", sa.String(length=255), nullable=True))
    op.add_column("message_attachments", sa.Column("extension", sa.String(length=20), nullable=True))
    op.add_column("message_attachments", sa.Column("size_bytes", sa.BigInteger(), nullable=True))
    op.add_column("message_attachments", sa.Column("checksum_sha256", sa.String(length=64), nullable=True))
    op.add_column(
        "message_attachments",
        sa.Column("download_status", sa.String(length=20), nullable=False, server_default="not_requested"),
    )
    op.add_column("message_attachments", sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("message_attachments", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.add_column("message_attachments", sa.Column("caption", sa.Text(), nullable=True))
    op.add_column("message_attachments", sa.Column("provider_timestamp", sa.DateTime(timezone=True), nullable=True))

    op.alter_column("message_attachments", "file_data", existing_type=postgresql.BYTEA(), nullable=True)

    op.execute(
        """
        UPDATE message_attachments
        SET
            filename = COALESCE(filename, file_name),
            extension = COALESCE(extension, file_extension),
            size_bytes = COALESCE(size_bytes, file_size_bytes),
            metadata_json = COALESCE(metadata_json, metadata_jsonb),
            duration_ms = COALESCE(duration_ms, duration_seconds * 1000),
            storage_backend = CASE
                WHEN file_data IS NOT NULL THEN 'db'
                WHEN provider_url IS NOT NULL THEN 'provider'
                ELSE COALESCE(storage_backend, 'none')
            END
        """
    )

    op.create_table(
        "attachment_blobs",
        sa.Column("attachment_id", sa.UUID(), nullable=False),
        sa.Column("binary_data", postgresql.BYTEA(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["attachment_id"], ["message_attachments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attachment_id", name="uq_attachment_blobs_attachment_id"),
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT id, file_data, COALESCE(updated_at, created_at, now()) AS created_at
            FROM message_attachments
            WHERE file_data IS NOT NULL
            """
        )
    ).mappings()
    for row in rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO attachment_blobs (id, attachment_id, binary_data, created_at)
                VALUES (:id, :attachment_id, :binary_data, :created_at)
                """
            ),
            {
                "id": uuid.uuid4(),
                "attachment_id": row["id"],
                "binary_data": row["file_data"],
                "created_at": row["created_at"],
            },
        )

    op.create_index("ix_message_attachments_message_id", "message_attachments", ["message_id"], unique=False)
    op.create_index("ix_message_attachments_provider_media_id", "message_attachments", ["provider_media_id"], unique=False)
    op.create_index("ix_message_attachments_checksum_sha256", "message_attachments", ["checksum_sha256"], unique=False)
    op.create_index("ix_message_attachments_download_status", "message_attachments", ["download_status"], unique=False)

    op.alter_column("message_attachments", "storage_backend", server_default=None)
    op.alter_column("message_attachments", "download_status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_message_attachments_download_status", table_name="message_attachments")
    op.drop_index("ix_message_attachments_checksum_sha256", table_name="message_attachments")
    op.drop_index("ix_message_attachments_provider_media_id", table_name="message_attachments")
    op.drop_index("ix_message_attachments_message_id", table_name="message_attachments")

    op.execute(
        """
        UPDATE message_attachments ma
        SET file_data = ab.binary_data
        FROM attachment_blobs ab
        WHERE ab.attachment_id = ma.id
        """
    )
    op.drop_table("attachment_blobs")

    op.drop_column("message_attachments", "provider_timestamp")
    op.drop_column("message_attachments", "caption")
    op.drop_column("message_attachments", "duration_ms")
    op.drop_column("message_attachments", "metadata_json")
    op.drop_column("message_attachments", "download_status")
    op.drop_column("message_attachments", "checksum_sha256")
    op.drop_column("message_attachments", "size_bytes")
    op.drop_column("message_attachments", "extension")
    op.drop_column("message_attachments", "filename")
    op.drop_column("message_attachments", "provider_url")
    op.drop_column("message_attachments", "provider_media_id")
    op.drop_column("message_attachments", "storage_key")
    op.drop_column("message_attachments", "storage_backend")

    op.alter_column("message_attachments", "file_data", existing_type=postgresql.BYTEA(), nullable=False)
