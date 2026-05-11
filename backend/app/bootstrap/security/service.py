from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.bootstrap.security.catalog import (
    ADMIN_PERMISSION_CODES,
    ADMIN_ROLE_NAME,
    BACKDOOR_ROLE_NAME,
    PERMISSIONS,
    ROLE_DEFINITIONS,
)
from app.bootstrap.security.repository import SecurityBootstrapRepository
from app.core.config import settings
from app.models.user import UserType
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


@dataclass
class BootstrapResult:
    created_permissions: int = 0
    created_roles: int = 0
    created_backdoor_user: bool = False


class SecurityBootstrapService:
    def __init__(self, db: Session) -> None:
        self.repo = SecurityBootstrapRepository(db)

    def run(self) -> BootstrapResult:
        result = BootstrapResult()
        try:
            permissions_by_code = self._seed_permissions(result)
            backdoor_role = self._seed_roles_and_permissions(permissions_by_code, result)
            self._seed_backdoor_user(backdoor_role, result)
            self.repo.commit()
            return result
        except Exception:
            self.repo.rollback()
            raise

    def _seed_permissions(self, result: BootstrapResult) -> dict[str, object]:
        permissions_by_code = {permission.code: permission for permission in self.repo.list_permissions()}
        for definition in PERMISSIONS:
            existing = permissions_by_code.get(definition.code)
            if existing is None:
                existing = self.repo.create_permission(
                    code=definition.code,
                    name=definition.name,
                    description=definition.description,
                )
                permissions_by_code[definition.code] = existing
                result.created_permissions += 1
                continue

            has_changes = False
            if existing.name != definition.name:
                existing.name = definition.name
                has_changes = True
            if existing.description != definition.description:
                existing.description = definition.description
                has_changes = True
            if has_changes:
                logger.info("Updated permission metadata for code=%s", definition.code)

        return permissions_by_code

    def _seed_roles_and_permissions(self, permissions_by_code: dict[str, object], result: BootstrapResult):
        roles = {}
        for role_name, role_description in ROLE_DEFINITIONS.items():
            role = self.repo.get_role_by_name(role_name)
            if role is None:
                role = self.repo.create_global_role(role_name, role_description, is_system=True)
                result.created_roles += 1
            else:
                role.description = role_description
                role.is_system = True
            roles[role_name] = role

        all_permissions = list(permissions_by_code.values())
        admin_permissions = [permissions_by_code[code] for code in ADMIN_PERMISSION_CODES if code in permissions_by_code]

        self.repo.set_role_permissions(roles[BACKDOOR_ROLE_NAME], all_permissions)
        self.repo.set_role_permissions(roles[ADMIN_ROLE_NAME], admin_permissions)

        return roles[BACKDOOR_ROLE_NAME]

    def _seed_backdoor_user(self, backdoor_role, result: BootstrapResult) -> None:
        email = settings.INITIAL_BACKDOOR_EMAIL
        password = settings.INITIAL_BACKDOOR_PASSWORD
        if not email or not password:
            if settings.is_production:
                raise RuntimeError(
                    "INITIAL_BACKDOOR_EMAIL and INITIAL_BACKDOOR_PASSWORD are required in production."
                )
            logger.warning("Skipping backdoor bootstrap user: missing INITIAL_BACKDOOR_EMAIL or password.")
            return

        user = self.repo.get_user_by_email(email)
        if user is None:
            user = self.repo.create_backdoor_user(
                name=settings.INITIAL_BACKDOOR_NAME,
                email=email,
                password_hash=hash_password(password),
                user_type=UserType.BACKDOOR,
            )
            result.created_backdoor_user = True
        else:
            user.name = settings.INITIAL_BACKDOOR_NAME
            user.is_active = True
            user.is_backdoor = True
            user.user_type = UserType.BACKDOOR
            if user.password_hash is None:
                user.password_hash = hash_password(password)

        link = self.repo.get_tenant_user_link(user.id, backdoor_role.id)
        if link is None:
            self.repo.create_global_tenant_user_link(user.id, backdoor_role.id)

