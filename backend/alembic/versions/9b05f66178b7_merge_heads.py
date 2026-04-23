"""merge heads

Revision ID: 9b05f66178b7
Revises: a69d78c70b8c
Create Date: 2026-04-23 18:06:07.002042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b05f66178b7'
down_revision: Union[str, None] = 'a69d78c70b8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
