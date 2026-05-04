import uuid
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Permission, Role, RolePermission, Tenant, TenantUser, User, UserPermission


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    stmt = select(User).where(func.lower(User.email) == email.lower())
    return db.execute(stmt).scalar_one_or_none()


def get_role_by_id(db: Session, role_id: uuid.UUID) -> Optional[Role]:
    return db.get(Role, role_id)


def get_tenant_by_id(db: Session, tenant_id: uuid.UUID) -> Optional[Tenant]:
    return db.get(Tenant, tenant_id)


def get_permissions_by_ids(db: Session, permission_ids: list[uuid.UUID]) -> list[Permission]:
    stmt = select(Permission).where(Permission.id.in_(permission_ids))
    return db.execute(stmt).scalars().all()


def add_user(
    db: Session,
    *,
    name: str,
    email: str,
    password_hash: str,
    is_active: bool,
    is_backdoor: bool,
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        is_active=is_active,
        is_backdoor=is_backdoor,
    )
    db.add(user)
    return user


def get_tenant_user_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[TenantUser]:
    stmt = select(TenantUser).where(TenantUser.user_id == user_id).limit(1)
    return db.execute(stmt).scalar_one_or_none()


def add_tenant_user(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    role_id: Optional[uuid.UUID],
) -> TenantUser:
    tenant_user = TenantUser(
        tenant_id=tenant_id,
        user_id=user_id,
        role_id=role_id,
    )
    db.add(tenant_user)
    return tenant_user


def add_user_permission(
    db: Session,
    *,
    tenant_user_id: uuid.UUID,
    permission_id: uuid.UUID,
    allowed: bool = True,
) -> UserPermission:
    user_permission = UserPermission(
        tenant_user_id=tenant_user_id,
        permission_id=permission_id,
        allowed=allowed,
    )
    db.add(user_permission)
    return user_permission


def delete_tenant_users_by_user_id(db: Session, user_id: uuid.UUID) -> None:
    db.execute(delete(TenantUser).where(TenantUser.user_id == user_id))


def delete_user_permissions_by_tenant_user_id(db: Session, tenant_user_id: uuid.UUID) -> None:
    db.execute(delete(UserPermission).where(UserPermission.tenant_user_id == tenant_user_id))


def delete_user(db: Session, user: User) -> None:
    db.delete(user)


def load_user_with_relations(db: Session, user_id: uuid.UUID) -> Optional[User]:
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


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
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
    return db.execute(stmt).unique().scalars().all()


def flush(db: Session) -> None:
    db.flush()


def commit(db: Session) -> None:
    db.commit()


def rollback(db: Session) -> None:
    db.rollback()
