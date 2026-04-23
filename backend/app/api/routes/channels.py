import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.permissions import require_permission
from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.channel import ChannelCreate, ChannelResponse, ChannelUpdate
from app.services.channel_service import (
    create_channel,
    delete_channel,
    get_channels,
    update_channel,
)

router = APIRouter(tags=["channels"])


@router.get("/", response_model=list[ChannelResponse])
async def read_channels(
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user),
    _: None = Depends(require_permission("channels.read")),
):
    user_id, _ = current_user
    user = db.get(User, user_id)
    return get_channels(db, user=user)


@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_endpoint(
    channel_data: ChannelCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("channels.create")),
):
    try:
        return create_channel(
            db=db,
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
    _: None = Depends(require_permission("channels.update")),
):
    try:
        channel = update_channel(
            db=db,
            channel_id=channel_id,
            **channel_data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_endpoint(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("channels.delete")),
):
    success = delete_channel(db, channel_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )
