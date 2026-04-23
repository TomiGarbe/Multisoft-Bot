"""add description and is_active to tenants

Revision ID: b2c4e6f8a0d1
Revises: f5a2c3b8d9e1
Create Date: 2026-04-22 17:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c4e6f8a0d1"
down_revision: Union[str, None] = "f5a2c3b8d9e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("tenants", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_column("tenants", "is_active")
    op.drop_column("tenants", "description")
