import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.channel import (
    ChannelConfigBundleResponse,
    ChannelCreate,
    ChannelResponse,
    ChannelUpdate,
)
from app.services.channel_service import ChannelService

router = APIRouter(tags=["channels"])


@router.get("/", response_model=list[ChannelResponse])
async def read_channels(
    db: Session = Depends(get_db),
):
    service = ChannelService(db)
    return service.get_channels(user=None)


@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_endpoint(
    channel_data: ChannelCreate,
    db: Session = Depends(get_db),
):
    service = ChannelService(db)
    try:
        return service.create_channel(
            tenant_id=channel_data.tenant_id,
            type=channel_data.type,
            name=channel_data.name,
            external_id=channel_data.external_id,
            config=channel_data.config,
            is_active=channel_data.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel_endpoint(
    channel_id: uuid.UUID,
    channel_data: ChannelUpdate,
    db: Session = Depends(get_db),
):
    service = ChannelService(db)
    try:
        channel = service.update_channel(
            channel_id=channel_id,
            **channel_data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return channel


@router.get("/{channel_id}/config", response_model=ChannelConfigBundleResponse)
async def get_channel_config_bundle(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = ChannelService(db)
    try:
        bundle = service.get_channel_config_bundle(channel_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        detail = str(exc)
        if detail in {"Config invalida", "Settings invalida", "User types invalido"}:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
        raise

    return bundle


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_endpoint(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = ChannelService(db)
    success = service.delete_channel(channel_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
