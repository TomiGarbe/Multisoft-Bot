import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.services.tenant_service import (
    create_tenant,
    delete_tenant,
    get_tenants,
    update_tenant,
)

router = APIRouter(tags=["tenants"])


@router.get("/", response_model=list[TenantResponse])
async def read_tenants(
    db: Session = Depends(get_db),
    #current_user: tuple = Depends(get_current_user),
    #_: None = Depends(require_permission("tenants.read")),
):
    #user_id, _ = current_user
    #user = db.get(User, user_id)
    return get_tenants(db, user=None)


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_endpoint(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    #_: None = Depends(require_permission("tenants.create")),
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
    #_: None = Depends(require_permission("tenants.update")),
):
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
    #_: None = Depends(require_permission("tenants.delete")),
):
    success = delete_tenant(db, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
