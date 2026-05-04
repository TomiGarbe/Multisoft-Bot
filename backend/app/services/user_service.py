import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Permission, Role, Tenant, User
from app.repositories import user_repository
from app.schemas.user import UserPermissionSummary, UserResponse, UserRoleSummary
from app.services.auth_service import hash_password


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return user_repository.get_user_by_id(db, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return user_repository.get_user_by_email(db, email)


def _validate_role(db: Session, role_id: Optional[uuid.UUID]) -> Optional[Role]:
    if role_id is None:
        return None
    role = user_repository.get_role_by_id(db, role_id)
    if role is None:
        raise LookupError("Role not found")
    return role


def _validate_permissions(db: Session, permission_ids: list[uuid.UUID]) -> list[Permission]:
    if not permission_ids:
        return []

    unique_ids = list(dict.fromkeys(permission_ids))
    permissions = user_repository.get_permissions_by_ids(db, unique_ids)
    if len(permissions) != len(unique_ids):
        found_ids = {permission.id for permission in permissions}
        missing = [str(pid) for pid in unique_ids if pid not in found_ids]
        raise LookupError(f"Invalid permission IDs: {', '.join(missing)}")
    return permissions


def _validate_tenant(db: Session, tenant_id: uuid.UUID) -> Tenant:
    tenant = user_repository.get_tenant_by_id(db, tenant_id)
    if tenant is None:
        raise LookupError("Tenant not found")
    return tenant


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
        tenant_id=tenant_link.tenant_id if tenant_link else None,
        role=role_data,
        permissions=list(permission_map.values()),
    )


def _load_user_with_relations(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return user_repository.load_user_with_relations(db, user_id)


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    role_id: Optional[uuid.UUID] = None,
    permissions: Optional[list[uuid.UUID]] = None,
    is_active: bool = True,
    is_backdoor: bool = False,
    tenant_id: Optional[uuid.UUID] = None,
) -> UserResponse:
    try:
        if get_user_by_email(db, email):
            raise ValueError("Email already registered")

        if is_backdoor and tenant_id is not None:
            raise ValueError("Backdoor user cannot be associated with a tenant")
        if is_backdoor and role_id is not None:
            raise ValueError("Backdoor user cannot have a tenant-scoped role")
        if is_backdoor and (permissions or []):
            raise ValueError("Backdoor user cannot have tenant-scoped direct permissions")

        if tenant_id is not None:
            _validate_tenant(db, tenant_id)

        role = _validate_role(db, role_id)
        permission_records = _validate_permissions(db, permissions or [])

        user = user_repository.add_user(
            db,
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_active=is_active,
            is_backdoor=is_backdoor,
        )
        user_repository.flush(db)

        if tenant_id is not None:
            tenant_user = user_repository.add_tenant_user(
                db,
                tenant_id=tenant_id,
                user_id=user.id,
                role_id=role.id if role else None,
            )
            user_repository.flush(db)

            for permission in permission_records:
                user_repository.add_user_permission(
                    db,
                    tenant_user_id=tenant_user.id,
                    permission_id=permission.id,
                    allowed=True,
                )

        user_repository.commit(db)
        loaded_user = _load_user_with_relations(db, user.id)
        if loaded_user is None:
            raise LookupError("User not found after creation")
        return _build_user_response(loaded_user)
    except Exception:
        user_repository.rollback(db)
        raise


def update_user(db: Session, user_id: uuid.UUID, **updates) -> Optional[UserResponse]:
    try:
        user = user_repository.get_user_by_id(db, user_id)
        if user is None:
            return None

        final_is_backdoor = updates.get("is_backdoor", user.is_backdoor)

        if final_is_backdoor and updates.get("role_id") is not None:
            raise ValueError("Backdoor user cannot have a tenant-scoped role")
        if final_is_backdoor and (updates.get("permissions") or []):
            raise ValueError("Backdoor user cannot have tenant-scoped direct permissions")
        if final_is_backdoor and updates.get("tenant_id") is not None:
            raise ValueError("Backdoor user cannot be associated with a tenant")

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

        if final_is_backdoor:
            user.is_backdoor = True
            user_repository.delete_tenant_users_by_user_id(db, user.id)
        else:
            user.is_backdoor = False

            role = None
            if "role_id" in updates:
                role_id = updates["role_id"]
                role = _validate_role(db, role_id) if role_id is not None else None

            incoming_tenant_id = updates.get("tenant_id")
            if incoming_tenant_id is not None:
                _validate_tenant(db, incoming_tenant_id)

            tenant_user = user_repository.get_tenant_user_by_user_id(db, user.id)

            if tenant_user is None and incoming_tenant_id is not None:
                tenant_user = user_repository.add_tenant_user(
                    db,
                    tenant_id=incoming_tenant_id,
                    user_id=user.id,
                    role_id=role.id if role else None,
                )
                user_repository.flush(db)
            elif tenant_user is not None:
                if incoming_tenant_id is not None and tenant_user.tenant_id != incoming_tenant_id:
                    tenant_user.tenant_id = incoming_tenant_id

                if "role_id" in updates:
                    tenant_user.role_id = role.id if role else None

            if tenant_user is not None and "permissions" in updates:
                permissions = updates["permissions"]
                permission_records = _validate_permissions(db, permissions or [])
                user_repository.delete_user_permissions_by_tenant_user_id(db, tenant_user.id)
                for permission in permission_records:
                    user_repository.add_user_permission(
                        db,
                        tenant_user_id=tenant_user.id,
                        permission_id=permission.id,
                        allowed=True,
                    )

        user_repository.commit(db)
        loaded_user = _load_user_with_relations(db, user.id)
        if loaded_user is None:
            return None
        return _build_user_response(loaded_user)
    except Exception:
        user_repository.rollback(db)
        raise


def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    try:
        user = user_repository.get_user_by_id(db, user_id)
        if user is None:
            return False

        user_repository.delete_user(db, user)
        user_repository.commit(db)
        return True
    except Exception:
        user_repository.rollback(db)
        raise


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    current_user_id: Optional[uuid.UUID] = None,
) -> list[UserResponse]:
    # DEV: tenant-scoped filtering disabled
    # if current_user_id is not None:
    #     caller = db.get(User, current_user_id)
    #     if caller and not caller.is_backdoor:
    #         # Normal user: only users that share at least one tenant
    #         caller_tenant_ids = (
    #             select(TenantUser.tenant_id)
    #             .where(TenantUser.user_id == current_user_id, TenantUser.tenant_id.is_not(None))
    #         )
    #         stmt = (
    #             select(User)
    #             .join(User.tenant_links)
    #             .where(TenantUser.tenant_id.in_(caller_tenant_ids))
    #             .offset(skip)
    #             .limit(limit)
    #             .options(*base_options)
    #         )
    #         users = db.execute(stmt).unique().scalars().all()
    #         return [_build_user_response(user) for user in users]

    users = user_repository.list_users(db, skip=skip, limit=limit)
    return [_build_user_response(user) for user in users]
