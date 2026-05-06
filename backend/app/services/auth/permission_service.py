import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import UserType
from app.repositories.auth_repository import AuthRepository

logger = logging.getLogger(__name__)


def _get_all_permission_codes(db: Session) -> set[str]:
    return AuthRepository(db).get_all_permission_codes()


def get_user_permissions(
    db: Session,
    tenant_user_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
) -> set[str]:
    """Resolve effective permissions for a tenant_user.

    Applies role-based permissions first, then user-level overrides
    (allowed=True adds, allowed=False removes).
    """
    repository = AuthRepository(db)
    if user_id is not None:
        user = repository.get_user_with_type(user_id)
        if user and user.user_type == UserType.BACKDOOR:
            permissions = _get_all_permission_codes(db)
            logger.debug(
                "Resolved all permissions for backdoor user %s: %s",
                user_id,
                permissions,
            )
            return permissions

    if tenant_user_id is None:
        logger.debug("tenant_user_id not provided")
        return set()

    tenant_user = repository.get_tenant_user_with_permissions(tenant_user_id=tenant_user_id)

    if not tenant_user:
        logger.debug("tenant_user %s not found", tenant_user_id)
        return set()

    if tenant_user.user and tenant_user.user.user_type == UserType.BACKDOOR:
        permissions = _get_all_permission_codes(db)
        logger.debug(
            "Resolved all permissions for backdoor tenant_user %s: %s",
            tenant_user_id,
            permissions,
        )
        return permissions

    # 1. Base permissions from role
    permissions: set[str] = set()
    if tenant_user.role_id and tenant_user.role:
        for rp in tenant_user.role.role_permissions:
            permissions.add(rp.permission.code)

    # 2. Apply user-level overrides
    for up in tenant_user.user_permissions:
        if up.allowed:
            permissions.add(up.permission.code)
        else:
            permissions.discard(up.permission.code)

    logger.debug(
        "Resolved permissions for tenant_user %s: %s",
        tenant_user_id,
        permissions,
    )
    return permissions
