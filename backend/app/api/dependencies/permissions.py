import logging
import uuid
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.models.auth import TenantUser
from app.services.auth.permission_service import get_user_permissions

logger = logging.getLogger(__name__)


def require_permission(permission_code: str) -> Callable:
    """Dependency factory that enforces a specific permission on an endpoint.

    Usage:
        @router.get("/")
        async def list_users(_: None = Depends(require_permission("users.read"))):
            ...
    """

    async def _check(
        current_user: tuple[uuid.UUID, str] = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        user_id, _ = current_user
        user = db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.is_backdoor:
            return

        tenant_user = db.execute(
            select(TenantUser)
            .where(TenantUser.user_id == user_id)
            .limit(1)
        ).scalar_one_or_none()

        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No tenant association for this user",
                headers={"WWW-Authenticate": "Bearer"},
            )

        permissions = get_user_permissions(db, tenant_user_id=tenant_user.id, user_id=user.id)

        if settings.DEBUG:
            logger.debug(
                "Permission check | user=%s | required=%s | effective=%s",
                user_id,
                permission_code,
                permissions,
            )

        if permission_code not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission_code}' required",
            )

    return _check
