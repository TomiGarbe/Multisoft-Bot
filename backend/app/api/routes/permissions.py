import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.schemas.permission import PermissionResponse
from app.services.permission_service import get_permission_by_id, get_permissions


router = APIRouter(tags=["permissions"])


@router.get("/", response_model=list[PermissionResponse])
async def read_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    return get_permissions(db, skip=skip, limit=limit)


@router.get("/{permission_id}", response_model=PermissionResponse)
async def read_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    permission = get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return permission
