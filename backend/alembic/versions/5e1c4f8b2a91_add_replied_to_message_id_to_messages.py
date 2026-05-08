"""add_replied_to_message_id_to_messages

Revision ID: 5e1c4f8b2a91
Revises: 4d680c0ca73a
Create Date: 2026-05-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e1c4f8b2a91'
down_revision: Union[str, None] = '4d680c0ca73a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('replied_to_message_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'replied_to_message_id')
