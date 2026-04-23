"""add backdoor flag to users

Revision ID: e3d6f0a2b7c1
Revises: c9f1b8a7d2e4
Create Date: 2026-04-22 16:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e3d6f0a2b7c1"
down_revision: Union[str, None] = "c9f1b8a7d2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_backdoor", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "is_backdoor", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "is_backdoor")
