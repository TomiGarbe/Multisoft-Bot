"""145_cleanup_legacy_ocr_capabilities

Revision ID: b1a2c3d4e5f6
Revises: 4f2b9a1c7d44
Create Date: 2026-05-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, None] = "4f2b9a1c7d44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM processed_artifacts
        WHERE capability NOT IN (
            'transcription',
            'metadata_extraction',
            'embeddings',
            'moderation',
            'thumbnails',
            'vision',
            'document_extraction'
        )
        """
    )
    op.execute(
        """
        DELETE FROM attachment_processing_jobs
        WHERE capability NOT IN (
            'transcription',
            'metadata_extraction',
            'embeddings',
            'moderation',
            'thumbnails',
            'vision',
            'document_extraction'
        )
        """
    )


def downgrade() -> None:
    # Irreversible cleanup of invalid legacy capability rows.
    pass
