from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Permission
from app.schemas.permission import PermissionResponse

INTERNAL_PERMISSION_CODES = {
    "users.create_admin",
    "users.create_backdoor",
    "tenants.create",
    "tenants.delete",
    "ai.test",
    "realtime.read",
}
GLOBAL_PERMISSION_PREFIXES = ("tenants.",)


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


def get_permission_metadata(code: str) -> dict[str, bool]:
    normalized = code.strip().lower()
    is_global = normalized.startswith(GLOBAL_PERMISSION_PREFIXES)
    is_internal = normalized in INTERNAL_PERMISSION_CODES or normalized.startswith("internal.")
    is_backdoor_only = normalized in {"users.create_backdoor"}
    tenant_visible = not (is_global or is_internal or is_backdoor_only)
    assignable = tenant_visible and normalized not in {"users.create_admin"}

    return {
        "assignable": assignable,
        "internal_only": is_internal,
        "backdoor_only": is_backdoor_only or is_global,
        "tenant_visible": tenant_visible,
    }


def serialize_permission(permission: Permission) -> PermissionResponse:
    metadata = get_permission_metadata(permission.code)
    return PermissionResponse(
        id=permission.id,
        code=permission.code,
        name=permission.name,
        description=permission.description,
        created_at=permission.created_at,
        **metadata,
    )
