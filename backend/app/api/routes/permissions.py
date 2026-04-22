import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.schemas.permission import (
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
)
from app.services.permission_service import (
    create_permission,
    delete_permission,
    get_permission_by_code,
    get_permission_by_id,
    get_permissions,
    update_permission,
)


router = APIRouter(tags=["permissions"])


@router.get("/", response_model=list[PermissionResponse])
async def read_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Get all permissions."""
    return get_permissions(db, skip=skip, limit=limit)


@router.post("/", response_model=PermissionResponse)
async def create_permission_endpoint(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Create a new permission."""
    existing = get_permission_by_code(db, permission_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission code already exists",
        )

    return create_permission(
        db,
        code=permission_data.code,
        name=permission_data.name,
        description=permission_data.description,
    )


@router.get("/{permission_id}", response_model=PermissionResponse)
async def read_permission(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Get permission by ID."""
    permission = get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return permission


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission_endpoint(
    permission_id: uuid.UUID,
    permission_data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Update permission."""
    permission = update_permission(
        db,
        permission_id,
        **permission_data.model_dump(exclude_unset=True),
    )
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return permission


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission_endpoint(
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Delete permission."""
    success = delete_permission(db, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
