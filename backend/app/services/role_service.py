import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models import Permission, Role, RolePermission
from app.schemas.role import RolePermissionSummary, RoleResponse


def get_role_by_id(db: Session, role_id: uuid.UUID) -> Optional[Role]:
    return db.get(Role, role_id)


def _validate_permissions(db: Session, permission_ids: list[uuid.UUID]) -> list[Permission]:
    if not permission_ids:
        return []

    unique_ids = list(dict.fromkeys(permission_ids))
    stmt = select(Permission).where(Permission.id.in_(unique_ids))
    permissions = db.execute(stmt).scalars().all()

    if len(permissions) != len(unique_ids):
        found_ids = {permission.id for permission in permissions}
        missing = [str(permission_id) for permission_id in unique_ids if permission_id not in found_ids]
        raise LookupError(f"Invalid permission IDs: {', '.join(missing)}")
    return permissions


def _load_role_with_permissions(db: Session, role_id: uuid.UUID) -> Optional[Role]:
    stmt = (
        select(Role)
        .where(Role.id == role_id)
        .options(joinedload(Role.role_permissions).joinedload(RolePermission.permission))
    )
    return db.execute(stmt).unique().scalars().first()


def _build_role_response(role: Role) -> RoleResponse:
    permissions = [
        RolePermissionSummary(
            id=role_permission.permission.id,
            code=role_permission.permission.code,
            name=role_permission.permission.name,
        )
        for role_permission in role.role_permissions
        if role_permission.permission is not None
    ]

    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=permissions,
    )


def create_role(
    db: Session,
    name: str,
    description: Optional[str] = None,
    permissions: Optional[list[uuid.UUID]] = None,
    tenant_id: Optional[uuid.UUID] = None,
) -> RoleResponse:
    try:
        permission_records = _validate_permissions(db, permissions or [])

        role = Role(
            tenant_id=tenant_id,
            name=name,
            description=description,
            is_system=False,
        )
        db.add(role)
        db.flush()

        for permission in permission_records:
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        db.commit()
        loaded_role = _load_role_with_permissions(db, role.id)
        if loaded_role is None:
            raise LookupError("Role not found after creation")
        return _build_role_response(loaded_role)
    except Exception:
        db.rollback()
        raise


def update_role(db: Session, role_id: uuid.UUID, **updates) -> Optional[RoleResponse]:
    try:
        role = db.get(Role, role_id)
        if role is None:
            return None

        if "name" in updates and updates["name"] is not None:
            role.name = updates["name"]
        if "description" in updates:
            role.description = updates["description"]

        if "permissions" in updates:
            permission_records = _validate_permissions(db, updates["permissions"] or [])
            db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
            for permission in permission_records:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        db.commit()
        loaded_role = _load_role_with_permissions(db, role.id)
        if loaded_role is None:
            return None
        return _build_role_response(loaded_role)
    except Exception:
        db.rollback()
        raise


def delete_role(db: Session, role_id: uuid.UUID) -> bool:
    try:
        role = db.get(Role, role_id)
        if role is None:
            return False

        db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
        db.delete(role)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> list[RoleResponse]:
    stmt = (
        select(Role)
        .offset(skip)
        .limit(limit)
        .options(joinedload(Role.role_permissions).joinedload(RolePermission.permission))
    )
    roles = db.execute(stmt).unique().scalars().all()
    return [_build_role_response(role) for role in roles]
