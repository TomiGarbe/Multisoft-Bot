"""143_contact_identities_tenant_isolation

Revision ID: 3a9d4b7e1c22
Revises: 8d2f5b53f6d1
Create Date: 2026-05-13 18:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3a9d4b7e1c22"
down_revision: Union[str, None] = "8d2f5b53f6d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contact_identities", sa.Column("tenant_id", sa.UUID(), nullable=True))

    op.execute(
        """
        UPDATE contact_identities ci
        SET tenant_id = c.tenant_id
        FROM contacts c
        WHERE c.id = ci.contact_id
        """
    )

    op.alter_column("contact_identities", "tenant_id", nullable=False)
    op.create_foreign_key(
        "fk_contact_identities_tenant_id_tenants",
        "contact_identities",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("uq_contact_identities_channel_external", "contact_identities", type_="unique")
    op.create_unique_constraint(
        "uq_contact_identities_tenant_channel_external",
        "contact_identities",
        ["tenant_id", "channel_type", "external_id"],
    )
    op.create_index(
        "ix_contact_identities_tenant_channel_external",
        "contact_identities",
        ["tenant_id", "channel_type", "external_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_contact_identities_tenant_channel_external", table_name="contact_identities")
    op.drop_constraint("uq_contact_identities_tenant_channel_external", "contact_identities", type_="unique")
    op.create_unique_constraint(
        "uq_contact_identities_channel_external",
        "contact_identities",
        ["channel_type", "external_id"],
    )
    op.drop_constraint("fk_contact_identities_tenant_id_tenants", "contact_identities", type_="foreignkey")
    op.drop_column("contact_identities", "tenant_id")
