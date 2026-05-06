import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant, get_current_user
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.models import User
from app.schemas.channel_config import (
    ChannelConfigResponse,
    ChannelConfigUpdate,
    ChannelConfigValidationStatusResponse,
)
from app.services.channel_config_service import ChannelConfigService

router = APIRouter(tags=["channel-config"])


@router.get(
    "/{id}",
    response_model=ChannelConfigResponse,
)
async def get_channel_config(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    __: None = Depends(require_permission("channel_config.read")),
):
    try:
        return ChannelConfigService.get_channel_config_by_id_and_tenant(
            db=db,
            config_id=id,
            tenant_id=current_tenant_id,
            user=current_user,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.put(
    "/{id}",
    response_model=ChannelConfigResponse,
)
async def update_channel_config(
    id: uuid.UUID,
    payload: ChannelConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    __: None = Depends(require_permission("channel_config.update")),
):
    try:
        return ChannelConfigService.update_channel_config(
            db=db,
            config_id=id,
            tenant_id=current_tenant_id,
            payload=payload,
            user=current_user,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/{id}/status",
    response_model=ChannelConfigValidationStatusResponse,
)
async def get_channel_config_status(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    __: None = Depends(require_permission("channel_config.read")),
):
    try:
        return ChannelConfigService.get_channel_config_status(
            db=db,
            config_id=id,
            tenant_id=current_tenant_id,
            user=current_user,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
