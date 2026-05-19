from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bootstrap.security.catalog import PERMISSION_UI_METADATA
from app.models import Permission
from app.schemas.permission import PermissionResponse

GLOBAL_PERMISSION_PREFIXES = ("tenants.",)
HIDDEN_ALIAS_CODES = {
    "manage_tenants",
    "create_tenants",
    "delete_tenants",
    "tenant_admin",
    "create_admins",
    "manage_superadmins",
    "create_backdoors",
    "manage_backdoors",
    "global_users",
    "backdoor_access",
    "test_ai",
    "debug_ai",
    "internal_ai_tools",
}


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


def get_permission_metadata(code: str) -> dict[str, object]:
    normalized = code.strip().lower()
    metadata = PERMISSION_UI_METADATA.get(normalized)
    module = metadata.module if metadata else (normalized.split(".", 1)[0] if "." in normalized else normalized)
    pages = list(metadata.pages) if metadata else []
    is_global = normalized.startswith(GLOBAL_PERMISSION_PREFIXES)
    is_internal = bool(metadata.internal_only) if metadata else normalized.startswith("internal.")
    is_backdoor_only = bool(metadata.backdoor_only) if metadata else False
    tenant_visible = bool(metadata.tenant_visible) if metadata else not (is_global or is_internal or is_backdoor_only)
    assignable = bool(metadata.assignable) if metadata else tenant_visible
    if normalized in HIDDEN_ALIAS_CODES:
        is_internal = True
        tenant_visible = False
        assignable = False

    return {
        "module": module,
        "pages": pages,
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
