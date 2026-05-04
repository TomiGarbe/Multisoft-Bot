import uuid
from typing import Optional

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import joinedload

from app.models import Permission, Role, RolePermission
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository):
    def get_by_id(self, role_id: uuid.UUID) -> Optional[Role]:
        return super().get_by_id(Role, role_id)

    def get_by_id_with_permissions(self, role_id: uuid.UUID) -> Optional[Role]:
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(joinedload(Role.role_permissions).joinedload(RolePermission.permission))
        )
        return self.db.execute(stmt).unique().scalars().first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Role]:
        stmt = (
            select(Role)
            .offset(skip)
            .limit(limit)
            .options(joinedload(Role.role_permissions).joinedload(RolePermission.permission))
        )
        return self.db.execute(stmt).unique().scalars().all()

    def get_all_by_tenant(self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Role]:
        stmt = (
            select(Role)
            .where(or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)))
            .offset(skip)
            .limit(limit)
            .options(joinedload(Role.role_permissions).joinedload(RolePermission.permission))
        )
        return self.db.execute(stmt).unique().scalars().all()

    def get_permissions_by_ids(self, permission_ids: list[uuid.UUID]) -> list[Permission]:
        if not permission_ids:
            return []
        stmt = select(Permission).where(Permission.id.in_(permission_ids))
        return self.db.execute(stmt).scalars().all()

    def create(self, role: Role) -> Role:
        self.db.add(role)
        return role

    def update(self, role: Role, **kwargs) -> Role:
        for key, value in kwargs.items():
            setattr(role, key, value)
        return role

    def delete(self, role: Role) -> None:
        super().delete(role)

    def create_role_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> RolePermission:
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        self.db.add(role_permission)
        return role_permission

    def delete_role_permissions(self, role_id: uuid.UUID) -> None:
        self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
