"""146_fix_user_type_enum_user_label

Revision ID: c2f6a8d9e701
Revises: b1a2c3d4e5f6
Create Date: 2026-05-19 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c2f6a8d9e701"
down_revision: Union[str, None] = "b1a2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'USER'
            ) THEN
                ALTER TYPE user_type_enum RENAME VALUE 'USER' TO 'User';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'ADMIN'
            ) THEN
                ALTER TYPE user_type_enum RENAME VALUE 'ADMIN' TO 'Administrador';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'BACKDOOR'
            ) THEN
                ALTER TYPE user_type_enum RENAME VALUE 'BACKDOOR' TO 'Backdoor';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'User'
            ) THEN
                ALTER TYPE user_type_enum RENAME VALUE 'User' TO 'USER';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'Administrador'
            ) THEN
                ALTER TYPE user_type_enum RENAME VALUE 'Administrador' TO 'ADMIN';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'Backdoor'
            ) THEN
                ALTER TYPE user_type_enum RENAME VALUE 'Backdoor' TO 'BACKDOOR';
            END IF;
        END
        $$;
        """
    )
