import logging
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Permission, User
from app.models.auth import RolePermission, TenantUser, UserPermission

logger = logging.getLogger(__name__)


def _get_all_permission_codes(db: Session) -> set[str]:
    stmt = select(Permission.code)
    return set(db.execute(stmt).scalars().all())


def get_user_permissions(
    db: Session,
    tenant_user_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
) -> set[str]:
    """Resolve effective permissions for a tenant_user.

    Applies role-based permissions first, then user-level overrides
    (allowed=True adds, allowed=False removes).
    """
    from app.models.auth import Role  # local import avoids any circular-import risk

    if user_id is not None:
        user = db.get(User, user_id)
        if user and user.is_backdoor:
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

    stmt = (
        select(TenantUser)
        .where(TenantUser.id == tenant_user_id)
        .options(
            joinedload(TenantUser.user),
            joinedload(TenantUser.role)
            .joinedload(Role.role_permissions)
            .joinedload(RolePermission.permission),
            joinedload(TenantUser.user_permissions)
            .joinedload(UserPermission.permission),
        )
    )
    tenant_user = db.execute(stmt).unique().scalar_one_or_none()

    if not tenant_user:
        logger.debug("tenant_user %s not found", tenant_user_id)
        return set()

    if tenant_user.user and tenant_user.user.is_backdoor:
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
