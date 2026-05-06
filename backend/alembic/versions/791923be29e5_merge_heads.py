"""merge heads

Revision ID: 791923be29e5
Revises: 137_ai_usage_events_refactor, 9f12d6b0c1a1
Create Date: 2026-05-05 23:53:02.378158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '791923be29e5'
down_revision: Union[str, None] = ('137_ai_usage_events_refactor', '9f12d6b0c1a1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
