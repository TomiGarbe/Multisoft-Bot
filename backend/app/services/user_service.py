import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Permission, Role, Tenant, User
from app.models.user import UserType
from app.repositories import user_repository
from app.schemas.user import TenantSummary, UserPermissionSummary, UserResponse, UserRoleSummary
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


def _normalize_user_type(user_type: Optional[UserType], is_backdoor: bool) -> UserType:
    if user_type is not None:
        return user_type
    return UserType.BACKDOOR if is_backdoor else UserType.USER


def _is_backdoor(user_type: UserType) -> bool:
    return user_type == UserType.BACKDOOR


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

    tenant_ids = [link.tenant_id for link in user.tenant_scopes]
    tenant_data = user.tenant_scopes[0].tenant if user.tenant_scopes else None

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        user_type=user.user_type,
        is_backdoor=user.is_backdoor,
        tenant_id=tenant_link.tenant_id if tenant_link else (tenant_ids[0] if tenant_ids else None),
        tenant_ids=tenant_ids,
        role=role_data,
        permissions=list(permission_map.values()),
        tenant=TenantSummary(id=tenant_data.id, name=tenant_data.name) if tenant_data else None,
        is_active=user.is_active,
    )


def _load_user_with_relations(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return user_repository.load_user_with_relations(db, user_id)


def get_user_response_by_id(db: Session, user_id: uuid.UUID) -> UserResponse:
    user = _load_user_with_relations(db, user_id)
    if user is None:
        raise LookupError("User not found")
    return _build_user_response(user)


def can_access_tenant(user: User, tenant_id: uuid.UUID) -> bool:
    if user.user_type == UserType.BACKDOOR:
        return True
    return tenant_id in {link.tenant_id for link in user.tenant_scopes}


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
    user_type: Optional[UserType] = None,
    tenant_ids: Optional[list[uuid.UUID]] = None,
) -> UserResponse:
    try:
        if get_user_by_email(db, email):
            raise ValueError("Email already registered")

        final_user_type = _normalize_user_type(user_type, is_backdoor)
        final_tenant_ids = list(dict.fromkeys(tenant_ids or ([] if tenant_id is None else [tenant_id])))

        if final_user_type == UserType.BACKDOOR:
            if role_id is not None or (permissions or []) or final_tenant_ids:
                raise ValueError("Backdoor user cannot have tenant-scoped associations")

        if final_user_type == UserType.ADMINISTRADOR and not final_tenant_ids:
            raise ValueError("Admin user must have at least one tenant assigned")

        if final_user_type == UserType.USER and len(final_tenant_ids) != 1:
            raise ValueError("User must belong to exactly one tenant")

        for tenant_link_id in final_tenant_ids:
            _validate_tenant(db, tenant_link_id)

        role = _validate_role(db, role_id)
        permission_records = _validate_permissions(db, permissions or [])

        user = user_repository.add_user(
            db,
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_active=is_active,
            is_backdoor=_is_backdoor(final_user_type),
            user_type=final_user_type,
        )
        user_repository.flush(db)

        if final_user_type in (UserType.ADMINISTRADOR, UserType.USER):
            for tenant_link_id in final_tenant_ids:
                user_repository.add_user_tenant_link(db, user_id=user.id, tenant_id=tenant_link_id)

        if final_user_type == UserType.USER:
            tenant_user = user_repository.add_tenant_user(
                db,
                tenant_id=final_tenant_ids[0],
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

        incoming_user_type = updates.get("user_type")
        incoming_is_backdoor = updates.get("is_backdoor")
        if incoming_user_type is None and incoming_is_backdoor is not None:
            incoming_user_type = UserType.BACKDOOR if incoming_is_backdoor else UserType.USER

        final_user_type = incoming_user_type or user.user_type

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

        requested_tenant_ids = updates.get("tenant_ids")
        if requested_tenant_ids is not None:
            requested_tenant_ids = list(dict.fromkeys(requested_tenant_ids))
            for tenant_link_id in requested_tenant_ids:
                _validate_tenant(db, tenant_link_id)

        if final_user_type == UserType.BACKDOOR:
            user.user_type = UserType.BACKDOOR
            user.is_backdoor = True
            user_repository.delete_tenant_users_by_user_id(db, user.id)
            user_repository.delete_user_tenant_links_by_user_id(db, user.id)

        elif final_user_type == UserType.ADMINISTRADOR:
            admin_tenant_ids = requested_tenant_ids or [link.tenant_id for link in user.tenant_scopes]
            if not admin_tenant_ids:
                raise ValueError("Admin user must have at least one tenant assigned")

            user.user_type = UserType.ADMINISTRADOR
            user.is_backdoor = False
            user_repository.delete_tenant_users_by_user_id(db, user.id)
            user_repository.delete_user_tenant_links_by_user_id(db, user.id)
            for tenant_link_id in admin_tenant_ids:
                user_repository.add_user_tenant_link(db, user_id=user.id, tenant_id=tenant_link_id)

        else:
            user_tenant_ids = requested_tenant_ids
            if user_tenant_ids is None:
                tenant_user = user_repository.get_tenant_user_by_user_id(db, user.id)
                user_tenant_ids = [tenant_user.tenant_id] if tenant_user else []
            if len(user_tenant_ids) != 1:
                raise ValueError("User must belong to exactly one tenant")

            role = None
            if "role_id" in updates:
                role_id = updates["role_id"]
                role = _validate_role(db, role_id) if role_id is not None else None

            user.user_type = UserType.USER
            user.is_backdoor = False
            user_repository.delete_user_tenant_links_by_user_id(db, user.id)
            user_repository.add_user_tenant_link(db, user_id=user.id, tenant_id=user_tenant_ids[0])

            tenant_user = user_repository.get_tenant_user_by_user_id(db, user.id)
            if tenant_user is None:
                tenant_user = user_repository.add_tenant_user(
                    db,
                    tenant_id=user_tenant_ids[0],
                    user_id=user.id,
                    role_id=role.id if role else None,
                )
                user_repository.flush(db)
            else:
                tenant_user.tenant_id = user_tenant_ids[0]
                if "role_id" in updates:
                    tenant_user.role_id = role.id if role else None

            if "permissions" in updates:
                permission_records = _validate_permissions(db, updates["permissions"] or [])
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
    users = user_repository.list_users(db, skip=skip, limit=limit)
    return [_build_user_response(user) for user in users]


def get_global_users(db: Session, skip: int = 0, limit: int = 100) -> list[UserResponse]:
    admin_users = user_repository.list_users_by_type(db, UserType.ADMINISTRADOR, skip=skip, limit=limit)
    backdoor_users = user_repository.list_users_by_type(db, UserType.BACKDOOR, skip=skip, limit=limit)
    return [_build_user_response(user) for user in [*admin_users, *backdoor_users]]


def get_tenant_users(db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[UserResponse]:
    _validate_tenant(db, tenant_id)
    users = user_repository.list_tenant_users(db, tenant_id=tenant_id, skip=skip, limit=limit)
    return [_build_user_response(user) for user in users]

