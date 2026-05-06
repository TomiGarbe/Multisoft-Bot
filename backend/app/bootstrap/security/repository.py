from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Permission, Role, RolePermission, TenantUser, User


class SecurityBootstrapRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_permission_by_code(self, code: str) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.code == code).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_permissions(self) -> list[Permission]:
        stmt = select(Permission)
        return self.db.execute(stmt).scalars().all()

    def create_permission(self, code: str, name: str, description: str) -> Permission:
        permission = Permission(code=code, name=name, description=description)
        self.db.add(permission)
        return permission

    def get_role_by_name(self, name: str) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name, Role.tenant_id.is_(None)).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_global_role(self, name: str, description: str, is_system: bool = True) -> Role:
        role = Role(name=name, description=description, tenant_id=None, is_system=is_system)
        self.db.add(role)
        self.db.flush()
        return role

    def set_role_permissions(self, role: Role, permissions: list[Permission]) -> None:
        target_ids = {permission.id for permission in permissions}
        existing = {item.permission_id: item for item in role.role_permissions}

        for permission_id, role_permission in existing.items():
            if permission_id not in target_ids:
                self.db.delete(role_permission)

        for permission in permissions:
            if permission.id not in existing:
                self.db.add(RolePermission(role_id=role.id, permission_id=permission.id))

    def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_backdoor_user(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        user_type,
    ) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            is_active=True,
            is_backdoor=True,
            user_type=user_type,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def get_tenant_user_link(self, user_id, role_id) -> Optional[TenantUser]:
        stmt = (
            select(TenantUser)
            .where(
                TenantUser.user_id == user_id,
                TenantUser.role_id == role_id,
                TenantUser.tenant_id.is_(None),
            )
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_global_tenant_user_link(self, user_id, role_id) -> TenantUser:
        link = TenantUser(user_id=user_id, role_id=role_id, tenant_id=None)
        self.db.add(link)
        return link

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
