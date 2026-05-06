import os
import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.repositories.auth_repository import AuthRepository
from app.services.auth.access_service import can_access_tenant, get_effective_permissions
from app.services.auth_service import verify_token

security = HTTPBearer()
_DEFAULT_DEV_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def _resolve_requested_tenant_id(
    tenant_id_query: Optional[str],
    tenant_id_header: Optional[str],
) -> uuid.UUID:
    requested = tenant_id_query or tenant_id_header or os.getenv("MULTISOFT_CURRENT_TENANT_ID", _DEFAULT_DEV_TENANT_ID)
    try:
        return uuid.UUID(str(requested))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant_id",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
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
    return user


async def get_current_user_identity(
    current_user: User = Depends(get_current_user),
) -> tuple[uuid.UUID, str]:
    return current_user.id, current_user.email


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
) -> uuid.UUID:
    resolved_tenant_id = _resolve_requested_tenant_id(tenant_id_query=None, tenant_id_header=x_tenant_id)
    if not can_access_tenant(db, current_user, resolved_tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )
    return resolved_tenant_id


def require_permission(permission_code: str):
    async def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    ) -> None:
        permissions = get_effective_permissions(db, current_user, tenant_id=current_tenant_id)
        if permission_code not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission_code}' required",
            )

    return _check
