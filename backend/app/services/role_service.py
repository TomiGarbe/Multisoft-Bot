from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role


def get_role_by_id(db: Session, role_id: uuid.UUID) -> Optional[Role]:
    """Get role by ID."""
    return db.get(Role, role_id)


def create_role(
    db: Session,
    name: str,
    description: Optional[str] = None,
    tenant_id: Optional[uuid.UUID] = None,
) -> Role:
    """Create a new role."""
    role = Role(
        tenant_id=tenant_id,
        name=name,
        description=description,
        is_system=False,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role_id: uuid.UUID, **kwargs) -> Optional[Role]:
    """Update role."""
    role = db.get(Role, role_id)
    if not role:
        return None

    for key, value in kwargs.items():
        if hasattr(role, key) and value is not None:
            setattr(role, key, value)

    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: uuid.UUID) -> bool:
    """Delete role."""
    role = db.get(Role, role_id)
    if not role:
        return False
    db.delete(role)
    db.commit()
    return True


def get_roles(db: Session, skip: int = 0, limit: int = 100):
    """Get all roles."""
    stmt = select(Role).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()
