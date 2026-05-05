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
    return UserType.BACKDOOR if is_backdoor else UserType.BUSINESS_USER


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

    business_ids = [link.business_id for link in user.business_links]
    tenant_data = None
    if user.business_links:
        business = user.business_links[0].business
        if business:
            tenant_data = TenantSummary(id=business.id, name=business.name)

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        user_type=user.user_type,
        is_backdoor=user.is_backdoor,
        tenant_id=tenant_link.tenant_id if tenant_link else (business_ids[0] if business_ids else None),
        business_ids=business_ids,
        role=role_data,
        permissions=list(permission_map.values()),
        tenant=tenant_data,
        is_active=user.is_active,
    )


def _load_user_with_relations(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return user_repository.load_user_with_relations(db, user_id)


def can_access_business(user: User, business_id: uuid.UUID) -> bool:
    if user.user_type == UserType.BACKDOOR:
        return True
    if user.user_type == UserType.ADMIN:
        return business_id in {link.business_id for link in user.business_links}
    if user.user_type == UserType.BUSINESS_USER:
        tenant_link = user.tenant_links[0] if user.tenant_links else None
        return bool(tenant_link and tenant_link.tenant_id == business_id)
    return False


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
    business_ids: Optional[list[uuid.UUID]] = None,
) -> UserResponse:
    try:
        if get_user_by_email(db, email):
            raise ValueError("Email already registered")

        final_user_type = _normalize_user_type(user_type, is_backdoor)
        final_business_ids = list(dict.fromkeys(business_ids or ([] if tenant_id is None else [tenant_id])))

        if final_user_type == UserType.BACKDOOR:
            if role_id is not None or (permissions or []) or final_business_ids:
                raise ValueError("Backdoor user cannot have business-scoped associations")

        if final_user_type == UserType.ADMIN and not final_business_ids:
            raise ValueError("Admin user must have at least one business assigned")

        if final_user_type == UserType.BUSINESS_USER:
            if len(final_business_ids) != 1:
                raise ValueError("Business user must belong to exactly one business")

        for business_id in final_business_ids:
            _validate_tenant(db, business_id)

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

        if final_user_type == UserType.ADMIN:
            for business_id in final_business_ids:
                user_repository.add_user_business(db, user_id=user.id, business_id=business_id)

        if final_user_type == UserType.BUSINESS_USER:
            tenant_user = user_repository.add_tenant_user(
                db,
                tenant_id=final_business_ids[0],
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
            incoming_user_type = UserType.BACKDOOR if incoming_is_backdoor else UserType.BUSINESS_USER

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

        requested_business_ids = updates.get("business_ids")
        if requested_business_ids is not None:
            requested_business_ids = list(dict.fromkeys(requested_business_ids))
            for business_id in requested_business_ids:
                _validate_tenant(db, business_id)

        if final_user_type == UserType.BACKDOOR:
            user.user_type = UserType.BACKDOOR
            user.is_backdoor = True
            user_repository.delete_tenant_users_by_user_id(db, user.id)
            user_repository.delete_user_businesses_by_user_id(db, user.id)

        elif final_user_type == UserType.ADMIN:
            admin_business_ids = requested_business_ids
            if admin_business_ids is None:
                admin_business_ids = [link.business_id for link in user.business_links]
            if not admin_business_ids:
                raise ValueError("Admin user must have at least one business assigned")

            user.user_type = UserType.ADMIN
            user.is_backdoor = False
            user_repository.delete_tenant_users_by_user_id(db, user.id)
            user_repository.delete_user_businesses_by_user_id(db, user.id)
            for business_id in admin_business_ids:
                user_repository.add_user_business(db, user_id=user.id, business_id=business_id)

        else:
            business_user_business_ids = requested_business_ids
            if business_user_business_ids is None:
                tenant_user = user_repository.get_tenant_user_by_user_id(db, user.id)
                business_user_business_ids = [tenant_user.tenant_id] if tenant_user else []
            if len(business_user_business_ids) != 1:
                raise ValueError("Business user must belong to exactly one business")

            role = None
            if "role_id" in updates:
                role_id = updates["role_id"]
                role = _validate_role(db, role_id) if role_id is not None else None

            user.user_type = UserType.BUSINESS_USER
            user.is_backdoor = False
            user_repository.delete_user_businesses_by_user_id(db, user.id)

            tenant_user = user_repository.get_tenant_user_by_user_id(db, user.id)
            if tenant_user is None:
                tenant_user = user_repository.add_tenant_user(
                    db,
                    tenant_id=business_user_business_ids[0],
                    user_id=user.id,
                    role_id=role.id if role else None,
                )
                user_repository.flush(db)
            else:
                tenant_user.tenant_id = business_user_business_ids[0]
                if "role_id" in updates:
                    tenant_user.role_id = role.id if role else None

            if "permissions" in updates:
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
    users = user_repository.list_users(db, skip=skip, limit=limit)
    return [_build_user_response(user) for user in users]


def get_global_users(db: Session, skip: int = 0, limit: int = 100) -> list[UserResponse]:
    admin_users = user_repository.list_users_by_type(db, UserType.ADMIN, skip=skip, limit=limit)
    backdoor_users = user_repository.list_users_by_type(db, UserType.BACKDOOR, skip=skip, limit=limit)
    return [_build_user_response(user) for user in [*admin_users, *backdoor_users]]


def get_business_users(db: Session, business_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[UserResponse]:
    _validate_tenant(db, business_id)
    users = user_repository.list_business_users(db, business_id=business_id, skip=skip, limit=limit)
    return [_build_user_response(user) for user in users]
