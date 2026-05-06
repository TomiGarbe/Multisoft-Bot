import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.schemas.ai import AITestRequest, AITestResponse
from app.services.ai.ai_service import AIService
from app.services.ai.prompt_builder import PromptBuilder
from app.services.channel_config_service import ChannelConfigService
from app.services.config_validation import get_config_validation_status
from app.services.message_service import MessageService
from app.services.quota_service import QuotaService

logger = logging.getLogger(__name__)

_DEFAULT_FALLBACK = "No pude procesar tu mensaje en este momento, podes intentar nuevamente?"


class AIOrchestrationService:
    def __init__(self, db: Session):
        self.db = db
        self.prompt_builder = PromptBuilder()
        self.message_service = MessageService(db)

    async def run_test(
        self,
        request: AITestRequest,
        tenant_id: uuid.UUID,
    ) -> AITestResponse:
        channel_config = ChannelConfigService.get_active_channel_config(self.db, request.channel_id)
        if channel_config.tenant_id != tenant_id:
            raise PermissionError("Channel access denied")

        config = channel_config.config_jsonb or {}
        settings_jsonb = channel_config.settings_jsonb or {}
        provider_name = settings_jsonb.get("ai_provider") if isinstance(settings_jsonb, dict) else None
        ai_service = AIService(provider_name=provider_name)
        validation_status = get_config_validation_status(config)
        if not validation_status["is_valid"]:
            missing_fields = ", ".join(validation_status["missing_fields"]) or "unknown"
            raise ValueError(f"Bot config is invalid for channel {request.channel_id} (missing: {missing_fields})")

        fallback_message = config.get("behavior", {}).get("fallback_message") or _DEFAULT_FALLBACK

        user_types_config = channel_config.user_types_jsonb or {}
        default_type = self._resolve_default_type(user_types_config)
        user_type = default_type
        user_memory = None

        if request.contact_id:
            contact = self.message_service.get_contact_by_id_and_tenant(request.contact_id, tenant_id)
            if contact:
                user_type = contact.current_type or default_type
                user_memory = contact.metadata_jsonb

        prompt = self.prompt_builder.build(
            config=config,
            messages=[],
            user_memory=user_memory,
            current_message=request.message,
            user_type=user_type,
        )

        response: Optional[str]
        quota_service = QuotaService(self.db)
        quota_decision = quota_service.can_use_ai(tenant_id=tenant_id)
        if not quota_decision.allowed:
            quota_message = (
                settings_jsonb.get("quota_exceeded_message")
                if isinstance(settings_jsonb, dict)
                else None
            ) or fallback_message
            logger.warning(
                "AI quota blocked test execution (tenant_id=%s reason=%s)",
                tenant_id,
                quota_decision.reason,
            )
            return AITestResponse(response=quota_message, prompt=prompt)

        try:
            response = await ai_service.generate(prompt)
        except Exception:
            logger.exception("AI generation failed during test for channel: %s", request.channel_id)
            response = None

        if not response or not response.strip():
            response = fallback_message

        return AITestResponse(response=response, prompt=prompt)

    @staticmethod
    def _resolve_default_type(user_types_config: dict) -> str:
        default_type = user_types_config.get("default_type")
        if default_type:
            return default_type
        types = user_types_config.get("types", [])
        default = next((t for t in types if t.get("is_default")), None)
        return default["key"] if default else "default"
