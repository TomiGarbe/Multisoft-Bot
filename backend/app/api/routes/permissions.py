import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.models import User
from app.schemas.permission import PermissionResponse
from app.services.auth.access_service import is_super_admin
from app.services.permission_service import get_permission_by_id, get_permissions, serialize_permission


router = APIRouter(tags=["permissions"])


@router.get("", response_model=list[PermissionResponse])
async def read_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("permissions.read")),
):
    is_global = is_super_admin(current_user)
    permissions = [serialize_permission(item) for item in get_permissions(db, skip=skip, limit=limit)]
    if is_global:
        return permissions
    return [permission for permission in permissions if permission.tenant_visible]


@router.get("/{permission_id}", response_model=PermissionResponse)
async def read_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("permissions.read")),
):
    permission = get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    response = serialize_permission(permission)
    if not is_super_admin(current_user) and not response.tenant_visible:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return response

