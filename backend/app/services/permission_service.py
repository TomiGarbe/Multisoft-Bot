from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Permission


def get_permission_by_id(db: Session, permission_id: uuid.UUID) -> Optional[Permission]:
    """Get permission by ID."""
    return db.get(Permission, permission_id)


def get_permission_by_code(db: Session, code: str) -> Optional[Permission]:
    """Get permission by code."""
    stmt = select(Permission).where(Permission.code == code)
    return db.execute(stmt).scalar_one_or_none()


def create_permission(
    db: Session, code: str, name: str, description: Optional[str] = None
) -> Permission:
    """Create a new permission."""
    permission = Permission(
        code=code,
        name=name,
        description=description,
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


def update_permission(db: Session, permission_id: uuid.UUID, **kwargs) -> Optional[Permission]:
    """Update permission."""
    permission = db.get(Permission, permission_id)
    if not permission:
        return None

    for key, value in kwargs.items():
        if hasattr(permission, key) and value is not None:
            setattr(permission, key, value)

    db.commit()
    db.refresh(permission)
    return permission


def delete_permission(db: Session, permission_id: uuid.UUID) -> bool:
    """Delete permission."""
    permission = db.get(Permission, permission_id)
    if not permission:
        return False
    db.delete(permission)
    db.commit()
    return True


def get_permissions(db: Session, skip: int = 0, limit: int = 100):
    """Get all permissions."""
    stmt = select(Permission).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()
