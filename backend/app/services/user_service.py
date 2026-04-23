import uuid
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Permission, Role, RolePermission, Tenant, TenantUser, User, UserPermission
from app.schemas.user import UserPermissionSummary, UserResponse, UserRoleSummary
from app.services.auth_service import hash_password


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    stmt = select(User).where(func.lower(User.email) == email.lower())
    return db.execute(stmt).scalar_one_or_none()


def _validate_role(db: Session, role_id: Optional[uuid.UUID]) -> Optional[Role]:
    if role_id is None:
        return None
    role = db.get(Role, role_id)
    if role is None:
        raise LookupError("Role not found")
    return role


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


def _resolve_tenant_id(db: Session, role: Optional[Role]) -> uuid.UUID:
    if role and role.tenant_id:
        return role.tenant_id

    tenant_stmt = select(Tenant.id).limit(1)
    tenant_id = db.execute(tenant_stmt).scalar_one_or_none()
    if tenant_id is None:
        raise LookupError("No tenant available to link user")
    return tenant_id


def _build_user_response(user: User) -> UserResponse:
    tenant_link = user.tenant_links[0] if user.tenant_links else None
    role = tenant_link.role if tenant_link else None

    role_permissions = []
    if role:
        role_permissions = [rp.permission for rp in role.role_permissions if rp.permission is not None]

    override_permissions = []
    if tenant_link:
        override_permissions = [
            up.permission for up in tenant_link.user_permissions if up.permission is not None and up.allowed
        ]

    permission_map: dict[uuid.UUID, UserPermissionSummary] = {}
    for permission in role_permissions + override_permissions:
        permission_map[permission.id] = UserPermissionSummary(
            id=permission.id,
            code=permission.code,
            name=permission.name,
        )

    role_data = None
    if role:
        role_data = UserRoleSummary(id=role.id, name=role.name, description=role.description)

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_backdoor=user.is_backdoor,
        role=role_data,
        permissions=list(permission_map.values()),
    )


def _load_user_with_relations(db: Session, user_id: uuid.UUID) -> Optional[User]:
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            joinedload(User.tenant_links)
            .joinedload(TenantUser.role)
            .joinedload(Role.role_permissions)
            .joinedload(RolePermission.permission),
            joinedload(User.tenant_links)
            .joinedload(TenantUser.user_permissions)
            .joinedload(UserPermission.permission),
        )
    )
    return db.execute(stmt).unique().scalars().first()


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    role_id: Optional[uuid.UUID] = None,
    permissions: Optional[list[uuid.UUID]] = None,
    is_active: bool = True,
    is_superadmin: bool = False,
    is_backdoor: bool = False,
) -> UserResponse:
    try:
        if get_user_by_email(db, email):
            raise ValueError("Email already registered")

        has_global_access = is_superadmin or is_backdoor
        if has_global_access and role_id is not None:
            raise ValueError("Global-access user cannot have tenant-scoped role")
        if has_global_access and (permissions or []):
            raise ValueError("Global-access user cannot have tenant-scoped direct permissions")

        role = _validate_role(db, role_id)
        permission_records = _validate_permissions(db, permissions or [])

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_active=is_active,
            is_superadmin=is_superadmin,
            is_backdoor=is_backdoor,
        )
        db.add(user)
        db.flush()

        if not has_global_access:
            tenant_id = _resolve_tenant_id(db, role)
            tenant_user = TenantUser(
                tenant_id=tenant_id,
                user_id=user.id,
                role_id=role.id if role else None,
                is_active=is_active,
            )
            db.add(tenant_user)
            db.flush()

            for permission in permission_records:
                db.add(
                    UserPermission(
                        tenant_user_id=tenant_user.id,
                        permission_id=permission.id,
                        allowed=True,
                    )
                )

        db.commit()
        loaded_user = _load_user_with_relations(db, user.id)
        if loaded_user is None:
            raise LookupError("User not found after creation")
        return _build_user_response(loaded_user)
    except Exception:
        db.rollback()
        raise


def update_user(db: Session, user_id: uuid.UUID, **updates) -> Optional[UserResponse]:
    try:
        user = db.get(User, user_id)
        if user is None:
            return None

        final_is_superadmin = updates.get("is_superadmin", user.is_superadmin)
        final_is_backdoor = updates.get("is_backdoor", user.is_backdoor)
        has_global_access = final_is_superadmin or final_is_backdoor
        if has_global_access and updates.get("role_id") is not None:
            raise ValueError("Global-access user cannot have tenant-scoped role")
        if has_global_access and (updates.get("permissions") or []):
            raise ValueError("Global-access user cannot have tenant-scoped direct permissions")

        if "email" in updates:
            email = updates["email"]
            if email is None:
                raise ValueError("Email cannot be null")
            if email.lower() != user.email.lower():
                existing = get_user_by_email(db, email)
                if existing and existing.id != user.id:
                    raise ValueError("Email already registered")
                user.email = email

        if "name" in updates and updates["name"] is not None:
            user.name = updates["name"]
        if "password" in updates and updates["password"] is not None:
            user.password_hash = hash_password(updates["password"])
        if "is_active" in updates and updates["is_active"] is not None:
            user.is_active = updates["is_active"]

        if has_global_access:
            user.is_superadmin = final_is_superadmin
            user.is_backdoor = final_is_backdoor
            db.execute(delete(TenantUser).where(TenantUser.user_id == user.id))
        else:
            user.is_superadmin = False
            user.is_backdoor = False

            role = None
            if "role_id" in updates:
                role_id = updates["role_id"]
                role = _validate_role(db, role_id) if role_id is not None else None

            tenant_user_stmt = select(TenantUser).where(TenantUser.user_id == user.id).limit(1)
            tenant_user = db.execute(tenant_user_stmt).scalar_one_or_none()
            if tenant_user is None:
                tenant_user = TenantUser(
                    tenant_id=_resolve_tenant_id(db, role),
                    user_id=user.id,
                    role_id=role.id if role else None,
                    is_active=user.is_active,
                )
                db.add(tenant_user)
                db.flush()

            if "is_active" in updates and updates["is_active"] is not None:
                tenant_user.is_active = updates["is_active"]

            if "role_id" in updates:
                tenant_user.role_id = role.id if role else None
                if role and role.tenant_id:
                    tenant_user.tenant_id = role.tenant_id
                elif tenant_user.tenant_id is None:
                    tenant_user.tenant_id = _resolve_tenant_id(db, role=None)

            if "permissions" in updates:
                permissions = updates["permissions"]
                permission_records = _validate_permissions(db, permissions or [])
                db.execute(delete(UserPermission).where(UserPermission.tenant_user_id == tenant_user.id))
                for permission in permission_records:
                    db.add(
                        UserPermission(
                            tenant_user_id=tenant_user.id,
                            permission_id=permission.id,
                            allowed=True,
                        )
                    )

        db.commit()
        loaded_user = _load_user_with_relations(db, user.id)
        if loaded_user is None:
            return None
        return _build_user_response(loaded_user)
    except Exception:
        db.rollback()
        raise


def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    try:
        user = db.get(User, user_id)
        if user is None:
            return False

        db.delete(user)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[UserResponse]:
    stmt = (
        select(User)
        .offset(skip)
        .limit(limit)
        .options(
            joinedload(User.tenant_links)
            .joinedload(TenantUser.role)
            .joinedload(Role.role_permissions)
            .joinedload(RolePermission.permission),
            joinedload(User.tenant_links)
            .joinedload(TenantUser.user_permissions)
            .joinedload(UserPermission.permission),
        )
    )
    users = db.execute(stmt).unique().scalars().all()
    return [_build_user_response(user) for user in users]
