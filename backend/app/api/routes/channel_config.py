import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.config import ChannelBotConfig
from app.schemas.bot_config import ChannelBotConfigResponse, ChannelBotConfigUpdate
from app.services.config_validation import get_config_validation_status

router = APIRouter(tags=["channel-config"])


class ChannelConfigValidationStatusResponse(BaseModel):
    is_valid: bool
    missing_fields: list[str]


@router.get(
    "/{id}",
    response_model=ChannelBotConfigResponse,
)
async def get_channel_config(
    id: uuid.UUID,
    db: Session = Depends(get_db),
):
    channel_config = db.get(ChannelBotConfig, id)
    if channel_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel config not found: {id}",
        )
    return channel_config


@router.put(
    "/{id}",
    response_model=ChannelBotConfigResponse,
)
async def update_channel_config(
    id: uuid.UUID,
    payload: ChannelBotConfigUpdate,
    db: Session = Depends(get_db),
):
    channel_config = db.get(ChannelBotConfig, id)
    if channel_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel config not found: {id}",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "config_jsonb" in update_data:
        channel_config.config_jsonb = update_data["config_jsonb"]
    if "settings_jsonb" in update_data:
        channel_config.settings_jsonb = update_data["settings_jsonb"]
    if "user_types_jsonb" in update_data:
        channel_config.user_types_jsonb = update_data["user_types_jsonb"]
    if "is_active" in update_data:
        channel_config.is_active = update_data["is_active"]

    db.commit()
    db.refresh(channel_config)
    return channel_config


@router.get(
    "/{id}/status",
    response_model=ChannelConfigValidationStatusResponse,
)
async def get_channel_config_status(
    id: uuid.UUID,
    db: Session = Depends(get_db),
):
    channel_config = db.get(ChannelBotConfig, id)
    if channel_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel config not found: {id}",
        )

    return get_config_validation_status(channel_config.config_jsonb)
