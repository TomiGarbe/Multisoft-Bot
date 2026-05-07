import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Role
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RolePermissionSummary, RoleResponse


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


class RoleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = RoleRepository(db)

    def _validate_permissions(self, permission_ids: list[uuid.UUID]) -> list[uuid.UUID]:
        if not permission_ids:
            return []

        unique_ids = list(dict.fromkeys(permission_ids))
        permissions = self.repository.get_permissions_by_ids(unique_ids)
        if len(permissions) != len(unique_ids):
            found_ids = {permission.id for permission in permissions}
            missing = [str(permission_id) for permission_id in unique_ids if permission_id not in found_ids]
            raise LookupError(f"Invalid permission IDs: {', '.join(missing)}")
        return unique_ids

    def get_role_by_id(self, role_id: uuid.UUID) -> Optional[Role]:
        return self.repository.get_by_id(role_id)

    def create_role(
        self,
        name: str,
        tenant_id: uuid.UUID,
        description: Optional[str] = None,
        permissions: Optional[list[uuid.UUID]] = None,
    ) -> RoleResponse:
        try:
            permission_ids = self._validate_permissions(permissions or [])

            role = Role(
                tenant_id=tenant_id,
                name=name,
                description=description,
                is_system=False,
            )
            self.repository.create(role)
            self.repository.flush()

            for permission_id in permission_ids:
                self.repository.create_role_permission(role.id, permission_id)

            self.repository.commit()
            loaded_role = self.repository.get_by_id_with_permissions(role.id)
            if loaded_role is None:
                raise LookupError("Role not found after creation")
            return _build_role_response(loaded_role)
        except Exception:
            self.repository.rollback()
            raise

    def update_role(self, role_id: uuid.UUID, tenant_id: uuid.UUID, **updates) -> Optional[RoleResponse]:
        try:
            role = self.repository.get_by_id_and_tenant_scope(role_id, tenant_id)
            if role is None:
                return None
            if role.tenant_id is None:
                raise PermissionError("System roles cannot be modified")

            mapped_updates: dict[str, object] = {}
            if "name" in updates and updates["name"] is not None:
                mapped_updates["name"] = updates["name"]
            if "description" in updates:
                mapped_updates["description"] = updates["description"]
            if mapped_updates:
                self.repository.update(role, **mapped_updates)

            if "permissions" in updates:
                permission_ids = self._validate_permissions(updates["permissions"] or [])
                self.repository.delete_role_permissions(role.id)
                for permission_id in permission_ids:
                    self.repository.create_role_permission(role.id, permission_id)

            self.repository.commit()
            loaded_role = self.repository.get_by_id_with_permissions(role.id)
            if loaded_role is None:
                return None
            return _build_role_response(loaded_role)
        except Exception:
            self.repository.rollback()
            raise

    def delete_role(self, role_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        try:
            role = self.repository.get_by_id_and_tenant_scope(role_id, tenant_id)
            if role is None:
                return False
            if role.tenant_id is None:
                raise PermissionError("System roles cannot be deleted")

            self.repository.delete_role_permissions(role.id)
            self.repository.delete(role)
            self.repository.commit()
            return True
        except Exception:
            self.repository.rollback()
            raise

    def get_roles(self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[RoleResponse]:
        roles = self.repository.get_all_by_tenant(tenant_id=tenant_id, skip=skip, limit=limit)
        return [_build_role_response(role) for role in roles]


def get_role_by_id(db: Session, role_id: uuid.UUID) -> Optional[Role]:
    return RoleService(db).get_role_by_id(role_id)


def create_role(
    db: Session,
    name: str,
    tenant_id: uuid.UUID,
    description: Optional[str] = None,
    permissions: Optional[list[uuid.UUID]] = None,
) -> RoleResponse:
    return RoleService(db).create_role(
        name=name,
        tenant_id=tenant_id,
        description=description,
        permissions=permissions,
    )


def update_role(db: Session, role_id: uuid.UUID, tenant_id: uuid.UUID, **updates) -> Optional[RoleResponse]:
    return RoleService(db).update_role(role_id=role_id, tenant_id=tenant_id, **updates)


def delete_role(db: Session, role_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
    return RoleService(db).delete_role(role_id=role_id, tenant_id=tenant_id)


def get_roles(db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[RoleResponse]:
    return RoleService(db).get_roles(tenant_id=tenant_id, skip=skip, limit=limit)
