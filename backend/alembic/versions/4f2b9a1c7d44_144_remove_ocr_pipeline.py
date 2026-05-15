"""144_remove_ocr_pipeline

Revision ID: 4f2b9a1c7d44
Revises: 3a9d4b7e1c22
Create Date: 2026-05-14 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "4f2b9a1c7d44"
down_revision: Union[str, None] = "3a9d4b7e1c22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM processed_artifacts WHERE capability = 'ocr'")
    op.execute("DELETE FROM attachment_processing_jobs WHERE capability = 'ocr'")

    op.execute(
        """
        UPDATE channel_bot_configs
        SET settings_jsonb = jsonb_set(
            COALESCE(settings_jsonb, '{}'::jsonb),
            '{media_processing}',
            (COALESCE(settings_jsonb->'media_processing', '{}'::jsonb) - 'ocr_enabled'),
            true
        )
        WHERE settings_jsonb IS NOT NULL
          AND settings_jsonb ? 'media_processing'
        """
    )

    op.execute(
        """
        UPDATE tenants
        SET features_jsonb = jsonb_set(
            COALESCE(features_jsonb, '{}'::jsonb),
            '{media_processing}',
            (COALESCE(features_jsonb->'media_processing', '{}'::jsonb) - 'ocr_enabled'),
            true
        )
        WHERE features_jsonb IS NOT NULL
          AND features_jsonb ? 'media_processing'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE channel_bot_configs
        SET settings_jsonb = jsonb_set(
            COALESCE(settings_jsonb, '{}'::jsonb),
            '{media_processing}',
            COALESCE(settings_jsonb->'media_processing', '{}'::jsonb) || '{"ocr_enabled": true}'::jsonb,
            true
        )
        """
    )

    op.execute(
        """
        UPDATE tenants
        SET features_jsonb = jsonb_set(
            COALESCE(features_jsonb, '{}'::jsonb),
            '{media_processing}',
            COALESCE(features_jsonb->'media_processing', '{}'::jsonb) || '{"ocr_enabled": true}'::jsonb,
            true
        )
        """
    )
