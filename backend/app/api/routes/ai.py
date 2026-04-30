import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.contact import Contact
from app.services.ai.ai_service import AIService
from app.services.ai.prompt_builder import PromptBuilder
from app.services.bot_config_service import BotConfigService
from app.services.config_validation import get_config_validation_status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI"])

_DEFAULT_FALLBACK = "No pude procesar tu mensaje en este momento, ¿podés intentar nuevamente?"


class AITestRequest(BaseModel):
    message: str
    channel_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None


class AITestResponse(BaseModel):
    response: str
    prompt: str


def _resolve_default_type(user_types_config: dict) -> str:
    default_type = user_types_config.get("default_type")
    if default_type:
        return default_type
    types = user_types_config.get("types", [])
    default = next((t for t in types if t.get("is_default")), None)
    return default["key"] if default else "default"


@router.post("/test", response_model=AITestResponse)
async def test_ai(
    body: AITestRequest,
    db: Session = Depends(get_db),
):
    channel_config = BotConfigService.get_active_channel_config(db, body.channel_id)
    if not channel_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active bot config found for channel {body.channel_id}",
        )
    config = channel_config.config_jsonb or {}

    validation_status = get_config_validation_status(config)
    if not validation_status["is_valid"]:
        missing_fields = ", ".join(validation_status["missing_fields"]) or "unknown"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bot config is invalid for channel {body.channel_id} (missing: {missing_fields})",
        )

    fallback_message = config.get("behavior", {}).get("fallback_message") or _DEFAULT_FALLBACK

    user_types_config = channel_config.user_types_jsonb or {}
    default_type = _resolve_default_type(user_types_config)

    user_type = default_type
    user_memory = None
    if body.contact_id:
        contact = db.get(Contact, body.contact_id)
        if contact:
            user_type = contact.current_type or default_type
            user_memory = contact.metadata_jsonb

    prompt_builder = PromptBuilder()
    prompt = prompt_builder.build(
        config=config,
        messages=[],
        user_memory=user_memory,
        current_message=body.message,
        user_type=user_type,
    )

    ai_service = AIService()
    try:
        response = await ai_service.generate(prompt)
    except Exception:
        logger.exception("AI generation failed during test for channel: %s", body.channel_id)
        response = None

    if not response or not response.strip():
        response = fallback_message

    return AITestResponse(response=response, prompt=prompt)
