import os
import uuid
from dataclasses import dataclass
from typing import Literal, Optional
import logging

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.core.datetime_utils import set_current_tenant_timezone
from app.repositories.auth_repository import AuthRepository
from app.repositories.tenant_repository import get_by_id as get_tenant_by_id
from app.services.auth.access_service import can_access_tenant, get_effective_permissions, is_super_admin
from app.services.auth_service import verify_token

security = HTTPBearer(auto_error=False)
_DEFAULT_DEV_TENANT_ID = "00000000-0000-0000-0000-000000000001"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TenantContext:
    tenant_id: Optional[uuid.UUID]
    requested_tenant_id: Optional[uuid.UUID]
    source: str
    is_super_admin: bool
    scope: Literal["tenant", "global"] = "tenant"


def _parse_requested_tenant_id(
    tenant_id_query: Optional[str],
    tenant_id_header: Optional[str],
) -> Optional[uuid.UUID]:
    requested = tenant_id_query or tenant_id_header
    if requested is None or not str(requested).strip():
        return None
    try:
        return uuid.UUID(str(requested))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant_id",
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Query(default=None, alias="access_token"),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials if credentials is not None else access_token
    if token is None or not str(token).strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token data",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = AuthRepository(db).get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug(
        "AUTH authenticated user=%s email=%s user_type=%s is_backdoor=%s",
        user.id,
        user.email,
        user.user_type.value,
        user.is_backdoor,
    )
    return user


async def get_current_user_identity(
    current_user: User = Depends(get_current_user),
) -> tuple[uuid.UUID, str]:
    return current_user.id, current_user.email


async def get_current_tenant_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    tenant_id_query: Optional[str] = Query(default=None, alias="tenant_id"),
    scope: str = Query(default="tenant"),
) -> TenantContext:
    normalized_scope = str(scope).strip().lower()
    if normalized_scope not in {"tenant", "global"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid scope")

    requested_tenant_id = _parse_requested_tenant_id(
        tenant_id_query=tenant_id_query,
        tenant_id_header=x_tenant_id,
    )
    user_is_super_admin = is_super_admin(current_user)

    if normalized_scope == "global":
        if not user_is_super_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Global scope access denied")
        set_current_tenant_timezone(None)
        return TenantContext(
            tenant_id=None,
            requested_tenant_id=requested_tenant_id,
            source="global_scope",
            is_super_admin=True,
            scope="global",
        )

    source = "header" if requested_tenant_id is not None else "default_tenant_link"
    resolved_tenant_id = requested_tenant_id

    if resolved_tenant_id is None:
        default_link = AuthRepository(db).get_default_tenant_user_link(user_id=current_user.id)
        if default_link is not None and default_link.tenant_id is not None:
            resolved_tenant_id = default_link.tenant_id
        else:
            fallback_tenant = os.getenv("MULTISOFT_CURRENT_TENANT_ID", _DEFAULT_DEV_TENANT_ID)
            if user_is_super_admin and fallback_tenant:
                try:
                    resolved_tenant_id = uuid.UUID(str(fallback_tenant))
                    source = "env_fallback"
                except (ValueError, TypeError):
                    resolved_tenant_id = None

    if resolved_tenant_id is None:
        detail = "X-Tenant-Id header required for this user"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    logger.debug(
        "AUTH tenant requested user=%s tenant=%s x_tenant_id=%s super_admin=%s source=%s",
        current_user.id,
        resolved_tenant_id,
        x_tenant_id,
        user_is_super_admin,
        source,
    )
    if not can_access_tenant(db, current_user, resolved_tenant_id):
        logger.debug("AUTH tenant denied user=%s tenant=%s", current_user.id, resolved_tenant_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )
    logger.debug("AUTH tenant granted user=%s tenant=%s", current_user.id, resolved_tenant_id)
    tenant = get_tenant_by_id(db, resolved_tenant_id)
    set_current_tenant_timezone(tenant.timezone if tenant else None)
    return TenantContext(
        tenant_id=resolved_tenant_id,
        requested_tenant_id=requested_tenant_id,
        source=source,
        is_super_admin=user_is_super_admin,
        scope="tenant",
    )


async def get_current_tenant(
    tenant_context: TenantContext = Depends(get_current_tenant_context),
) -> uuid.UUID:
    if tenant_context.scope != "tenant" or tenant_context.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant scope required")
    return tenant_context.tenant_id


def require_permission(permission_code: str):
    async def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        tenant_context: TenantContext = Depends(get_current_tenant_context),
    ) -> None:
        current_tenant_id = tenant_context.tenant_id
        permissions = get_effective_permissions(db, current_user, tenant_id=current_tenant_id)
        logger.debug(
            "AUTH permission check user=%s tenant=%s permission=%s super_admin=%s",
            current_user.id,
            current_tenant_id,
            permission_code,
            is_super_admin(current_user),
        )
        if permission_code not in permissions:
            logger.debug(
                "AUTH permission denied user=%s tenant=%s permission=%s",
                current_user.id,
                current_tenant_id,
                permission_code,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission_code}' required",
            )
        logger.debug(
            "AUTH permission granted user=%s tenant=%s permission=%s",
            current_user.id,
            current_tenant_id,
            permission_code,
        )

    return _check


async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> None:
    if not is_super_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
