import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant, get_current_user
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.models import User
from app.models.user import UserType
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.tenant_service import (
    create_tenant,
    delete_tenant,
    get_tenants,
    update_tenant,
)
from app.services.user_service import create_user, get_tenant_users, update_user

router = APIRouter(tags=["tenants"])


def _ensure_tenant_context(target_tenant_id: uuid.UUID, current_tenant_id: uuid.UUID) -> None:
    if target_tenant_id != current_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant access denied")


@router.get("/", response_model=list[TenantResponse])
async def read_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission("tenants.read")),
):
    return get_tenants(db, user=current_user)


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_endpoint(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("tenants.create")),
):

    try:
        return create_tenant(
            db=db,
            name=tenant_data.name,
            slug=tenant_data.slug,
            description=tenant_data.description,
            industry=tenant_data.industry,
            timezone=tenant_data.timezone,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant_endpoint(
    tenant_id: uuid.UUID,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("tenants.update")),
):
    _ensure_tenant_context(tenant_id, current_tenant_id)
    try:
        tenant = update_tenant(
            db=db,
            tenant_id=tenant_id,
            **tenant_data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_endpoint(
    tenant_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("tenants.delete")),
):
    _ensure_tenant_context(tenant_id, current_tenant_id)
    success = delete_tenant(db, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )


@router.get("/{tenant_id}/users", response_model=list[UserResponse])
async def read_tenant_users(
    tenant_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.read")),
):
    _ensure_tenant_context(tenant_id, current_tenant_id)
    try:
        return get_tenant_users(db, tenant_id=tenant_id, skip=skip, limit=limit)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{tenant_id}/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_user(
    tenant_id: uuid.UUID,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.create")),
):
    _ensure_tenant_context(tenant_id, current_tenant_id)
    try:
        return create_user(
            db=db,
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            role_id=user_data.role_id,
            permissions=user_data.permissions,
            is_active=user_data.is_active,
            user_type=UserType.USER,
            tenant_ids=[tenant_id],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{tenant_id}/users/{user_id}", response_model=UserResponse)
async def update_tenant_user(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: User = Depends(get_current_user),
    __: None = Depends(require_permission("users.update")),
):
    _ensure_tenant_context(tenant_id, current_tenant_id)
    try:
        payload = user_data.model_dump(exclude_unset=True)
        payload["user_type"] = UserType.USER
        payload["tenant_ids"] = [tenant_id]
        user = update_user(db=db, user_id=user_id, **payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
