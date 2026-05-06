"""bot-actions-phase-1-5-contracts

Revision ID: 139_bot_actions_phase_1_5_contracts
Revises: 138_bot_actions_foundation
Create Date: 2026-05-06 04:10:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "139_bot_actions_phase_1_5_contracts"
down_revision: Union[str, None] = "138_bot_actions_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_bot_actions_tenant_name",
        "bot_actions",
        ["tenant_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_bot_actions_tenant_name", "bot_actions", type_="unique")

