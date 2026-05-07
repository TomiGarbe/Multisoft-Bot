import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant, get_current_user
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.models import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.services.auth.access_service import can_operate_on_tenant_target
from app.services.api_key_service import ApiKeyService

router = APIRouter(tags=["api-keys"])


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("api_keys.manage")),
):
    return ApiKeyService(db).list_api_keys(current_tenant_id)


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("api_keys.manage")),
):
    if not can_operate_on_tenant_target(current_user, current_tenant_id, payload.tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant access denied")

    service = ApiKeyService(db)
    try:
        return service.create_api_key(
            tenant_id=payload.tenant_id,
            channel_id=payload.channel_id,
            name=payload.name,
            expires_at=payload.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("api_keys.manage")),
):
    if not ApiKeyService(db).revoke_api_key(tenant_id=current_tenant_id, api_key_id=api_key_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

