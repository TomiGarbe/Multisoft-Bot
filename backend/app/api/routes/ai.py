import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.contact import Contact
from app.services.ai.ai_service import AIService
from app.services.ai.prompt_builder import PromptBuilder
from app.services.bot_config_service import BotConfigService

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


def _get_user_memory(db: Session, contact_id: Optional[uuid.UUID]) -> Optional[dict]:
    if not contact_id:
        return None
    contact = db.get(Contact, contact_id)
    if not contact or not contact.metadata_jsonb:
        return None
    return contact.metadata_jsonb.get("memory")


@router.post("/test", response_model=AITestResponse)
async def test_ai(
    body: AITestRequest,
    db: Session = Depends(get_db),
):
    config = BotConfigService.get_active_channel_config(db, body.channel_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active bot config found for channel {body.channel_id}",
        )

    fallback_message = config.get("behavior", {}).get("fallback_message") or _DEFAULT_FALLBACK

    user_memory = _get_user_memory(db, body.contact_id)

    prompt_builder = PromptBuilder()
    prompt = prompt_builder.build(
        config=config,
        messages=[],
        user_memory=user_memory,
        current_message=body.message,
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
