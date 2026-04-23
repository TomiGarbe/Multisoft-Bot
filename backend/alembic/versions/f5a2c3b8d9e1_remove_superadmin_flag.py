"""Remove superadmin flag from users

Revision ID: f5a2c3b8d9e1
Revises: e3d6f0a2b7c1
Create Date: 2026-04-22 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f5a2c3b8d9e1"
down_revision: Union[str, None] = "e3d6f0a2b7c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "is_superadmin")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "is_superadmin", server_default=None)
