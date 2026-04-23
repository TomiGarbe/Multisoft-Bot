"""merge heads

Revision ID: b8847e4033fa
Revises: 9b05f66178b7, d1e2f3a4b5c6
Create Date: 2026-04-23 18:06:49.962431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8847e4033fa'
down_revision: Union[str, None] = ('9b05f66178b7', 'd1e2f3a4b5c6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
