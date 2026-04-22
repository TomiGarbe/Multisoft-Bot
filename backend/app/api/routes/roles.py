import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.services.role_service import (
    create_role,
    delete_role,
    get_role_by_id,
    get_roles,
    update_role,
)


router = APIRouter(tags=["roles"])


@router.get("/", response_model=list[RoleResponse])
async def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Get all roles."""
    return get_roles(db, skip=skip, limit=limit)


@router.post("/", response_model=RoleResponse)
async def create_role_endpoint(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Create a new role."""
    return create_role(
        db,
        name=role_data.name,
        description=role_data.description,
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def read_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Get role by ID."""
    role = get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role_endpoint(
    role_id: uuid.UUID,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Update role."""
    role = update_role(db, role_id, **role_data.model_dump(exclude_unset=True))
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_endpoint(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
):
    """Delete role."""
    success = delete_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
