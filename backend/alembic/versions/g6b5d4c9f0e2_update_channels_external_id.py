"""Update channels table with external_id and unique constraint

Revision ID: g6b5d4c9f0e2
Revises: f5a2c3b8d9e1
Create Date: 2026-04-23 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "g6b5d4c9f0e2"
down_revision: Union[str, None] = "f5a2c3b8d9e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename identifier column to external_id
    op.alter_column("channels", "identifier", new_column_name="external_id")
    
    # Add unique constraint on (tenant_id, external_id)
    op.create_unique_constraint(
        "uq_tenant_external_id",
        "channels",
        ["tenant_id", "external_id"],
    )


def downgrade() -> None:
    # Remove unique constraint
    op.drop_constraint("uq_tenant_external_id", "channels", type_="unique")
    
    # Rename external_id column back to identifier
    op.alter_column("channels", "external_id", new_column_name="identifier")
