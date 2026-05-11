"""rename user_type enum values to display names

Revision ID: 140_user_type_labels
Revises: 5e1c4f8b2a91
Create Date: 2026-05-11
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "140_user_type_labels"
down_revision: Union[str, None] = "5e1c4f8b2a91"
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

            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'USER'
            ) THEN
                ALTER TYPE user_type_enum RENAME VALUE 'USER' TO 'User';
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

            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'User'
            ) THEN
                ALTER TYPE user_type_enum RENAME VALUE 'User' TO 'USER';
            END IF;
        END
        $$;
        """
    )
