"""merge heads

Revision ID: c09acd32079d
Revises: 0ec4b247111b, g6b5d4c9f0e2
Create Date: 2026-04-23 14:58:42.358622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c09acd32079d'
down_revision: Union[str, None] = ('0ec4b247111b', 'g6b5d4c9f0e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
