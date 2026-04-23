"""add superadmin flag and nullable tenant_user tenant

Revision ID: c9f1b8a7d2e4
Revises: a1aebc810a53
Create Date: 2026-04-22 15:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9f1b8a7d2e4"
down_revision: Union[str, None] = "a1aebc810a53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "is_superadmin", server_default=None)
    op.alter_column("tenant_users", "tenant_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("tenant_users", "tenant_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("users", "is_superadmin")

