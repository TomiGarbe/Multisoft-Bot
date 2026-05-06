"""
Optional entrypoint to run the same automatic security bootstrap manually.
This script does not contain hardcoded seed data.
"""

import sys

from app.bootstrap.security import SecurityBootstrapService
from app.db.session import SessionLocal


def seed_database() -> bool:
    db = SessionLocal()
    try:
        result = SecurityBootstrapService(db).run()
        print(
            "Security bootstrap finished "
            f"(created_permissions={result.created_permissions}, "
            f"created_roles={result.created_roles}, "
            f"created_backdoor_user={result.created_backdoor_user})"
        )
        return True
    except Exception as exc:
        print(f"Security bootstrap failed: {exc}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1)
