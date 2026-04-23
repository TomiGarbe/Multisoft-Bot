import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.services.role_service import create_role, delete_role, get_roles, update_role


router = APIRouter(tags=["roles"])


@router.get("/", response_model=list[RoleResponse])
async def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("roles.read")),
):
    return get_roles(db, skip=skip, limit=limit)


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role_endpoint(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("roles.create")),
):
    try:
        return create_role(
            db=db,
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role_endpoint(
    role_id: uuid.UUID,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("roles.update")),
):
    try:
        role = update_role(
            db=db,
            role_id=role_id,
            **role_data.model_dump(exclude_unset=True),
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_endpoint(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("roles.delete")),
):
    success = delete_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
