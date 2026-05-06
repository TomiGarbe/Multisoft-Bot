"""add user_type and user_tenants

Revision ID: 9f12d6b0c1a1
Revises: 135c836ecfdd
Create Date: 2026-05-04 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9f12d6b0c1a1"
down_revision: Union[str, None] = "135c836ecfdd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_type_enum = sa.Enum("ADMIN", "BACKDOOR", "USER", name="user_type_enum")


def upgrade() -> None:
    bind = op.get_bind()

    user_type_enum.create(bind, checkfirst=True)
    op.add_column("users", sa.Column("user_type", user_type_enum, nullable=True))

    op.create_table(
        "user_tenants",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "tenant_id", name="uq_user_tenants_user_tenant"),
    )

    op.execute(
        """
        INSERT INTO user_tenants (user_id, tenant_id, created_at, updated_at)
        SELECT tu.user_id, tu.tenant_id, now(), now()
        FROM tenant_users tu
        WHERE tu.tenant_id IS NOT NULL
        ON CONFLICT (user_id, tenant_id) DO NOTHING
        """
    )

    op.execute(
        """
        WITH user_tenant_count AS (
          SELECT user_id, COUNT(DISTINCT tenant_id) AS tenant_count
          FROM tenant_users
          WHERE tenant_id IS NOT NULL
          GROUP BY user_id
        )
        UPDATE users u
        SET user_type = CASE
            WHEN u.is_backdoor THEN 'BACKDOOR'
            WHEN COALESCE(utc.tenant_count, 0) > 1 THEN 'ADMIN'
            WHEN COALESCE(utc.tenant_count, 0) = 1 THEN 'USER'
            ELSE 'ADMIN'
          END::user_type_enum
        FROM user_tenant_count utc
        WHERE u.id = utc.user_id
        """
    )

    op.execute(
        """
        UPDATE users
        SET user_type = CASE
            WHEN is_backdoor THEN 'BACKDOOR'
            ELSE 'ADMIN'
          END::user_type_enum
        WHERE user_type IS NULL
        """
    )

    op.execute("UPDATE users SET is_backdoor = (user_type = 'BACKDOOR')")

    op.alter_column("users", "user_type", nullable=False)


def downgrade() -> None:
    op.drop_table("user_tenants")
    op.drop_column("users", "user_type")
    user_type_enum.drop(op.get_bind(), checkfirst=True)
