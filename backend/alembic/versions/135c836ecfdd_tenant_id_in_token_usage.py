"""tenant-id-in-token-usage

Revision ID: 135c836ecfdd
Revises: 008_add_token_usage
Create Date: 2026-05-04 15:53:11.984681

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '135c836ecfdd'
down_revision: Union[str, None] = '008_add_token_usage'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Kept as no-op: token_usage is tenant-scoped since revision 008.
    pass


def downgrade() -> None:
    pass
