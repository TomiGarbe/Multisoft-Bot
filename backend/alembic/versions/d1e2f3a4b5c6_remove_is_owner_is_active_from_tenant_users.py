"""Remove is_owner and is_active from tenant_users

Revision ID: d1e2f3a4b5c6
Revises: c09acd32079d
Create Date: 2026-04-23 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c09acd32079d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("tenant_users", "is_owner")
    op.drop_column("tenant_users", "is_active")


def downgrade() -> None:
    op.add_column(
        "tenant_users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("tenant_users", "is_active", server_default=None)
    op.add_column(
        "tenant_users",
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("tenant_users", "is_owner", server_default=None)
