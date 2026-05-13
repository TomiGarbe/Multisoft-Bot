"""
AI response orchestration for inbound conversation flows.

Responsibilities:
1. Build prompt and call AI provider
2. Persist AI logs and token usage
3. Apply fallback / out-of-scope / max-bot-messages rules
4. Handle conversation mode transitions and contact user-type transitions
"""

import logging
import json
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation
from app.repositories.ai.ai_log_repository import AILogRepository
from app.services.ai.ai_service import AIService
from app.services.ai.debug_logger import (
    is_ai_debug_enabled,
    log_block,
    log_footer,
    log_header,
    make_debug_id,
    split_prompt_sections,
)
from app.services.ai.ai_tool_execution_service import AIToolExecutionService
from app.services.ai.ai_tool_registry_service import AIToolRegistryService
from app.services.ai.out_of_scope_detector import is_out_of_scope
from app.services.ai.prompt_builder import PromptBuilder
from app.services.quota_service import QuotaService
from app.services.usage_service import UsageService
from app.utils.ai_tool_constants import MAX_TOOL_CALLS_PER_MESSAGE
import app.services.message_service as message_service
from app.services.conversation.context_builder import build_conversation_context
from app.services.conversation.guards import should_use_ai
from app.services.conversation.mode_service import disable_ai
from app.services.config_structure import section_entries

logger = logging.getLogger(__name__)

_DEFAULT_FALLBACK = "No pude procesar tu mensaje en este momento, podes intentar nuevamente?"
_MAX_TOOL_LOOP_ITERATIONS = 1
_SYSTEM_TOOLS_INSTRUCTION = (
    "Si necesitas datos externos o de sistema, usa tools disponibles. "
    "No inventes resultados de tools."
)


class AIResponseOrchestrator:
    def __init__(self):
        self.prompt_builder = PromptBuilder()

    def build_prompt(self, config: dict, context: dict) -> str:
        return self.prompt_builder.build_prompt(config=config, context=context)

    def build_prompt_for_conversation(
        self,
        db: Session,
        conversation: Conversation,
        channel_config,
        current_message,
    ) -> Optional[str]:
        config = channel_config.config_jsonb or {}
        context = build_conversation_context(db, conversation, current_message, config)
        self._ensure_contact_default_type(
            db=db,
            contact_id=current_message.sender_contact_id,
            config=config,
            user_types=(channel_config.user_types_jsonb or {}),
        )
        prompt = self.build_prompt(config, context)
        if not prompt:
            logger.warning("Empty prompt for conversation: %s", conversation.id)
            return None
        return prompt

    async def call_ai(self, prompt: str, provider_name: str | None = None) -> dict[str, Any]:
        ai_service = AIService(provider_name=provider_name)
        return await ai_service.generate_with_metadata(prompt)

    async def call_ai_chat(
        self,
        *,
        prompt: str,
        current_user_message: str,
        provider_name: str | None,
        tools: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        ai_service = AIService(provider_name=provider_name)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "system", "content": _SYSTEM_TOOLS_INSTRUCTION},
            {"role": "user", "content": current_user_message},
        ]
        return await ai_service.generate_chat_with_metadata(messages, tools=tools)

    async def generate_response(
        self,
        db: Session,
        conversation: Conversation,
        channel_config,
        prompt: str,
        contact_id: Optional[uuid.UUID],
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
        message_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> Optional[str]:
        config = channel_config.config_jsonb or {}
        channel_settings = channel_config.settings_jsonb or {}
        debug_enabled = is_ai_debug_enabled()
        debug_id = make_debug_id() if debug_enabled else None
        provider_name = "ollama"
        if isinstance(channel_settings, dict):
            provider_name = str(channel_settings.get("ai_provider") or "ollama")

        behavior = config.get("behavior")
        fallback_message = (
            (behavior.get("fallback_message") if isinstance(behavior, dict) else None)
            or _DEFAULT_FALLBACK
        )

        response = None
        ai_payload: dict[str, Any] | None = None
        tool_names: list[str] = []
        if debug_enabled and debug_id is not None:
            log_header(
                debug_id=debug_id,
                metadata={
                    "tenant_id": str(tenant_id),
                    "channel_id": str(channel_id),
                    "conversation_id": str(conversation.id),
                    "contact_id": str(contact_id) if contact_id else None,
                    "request_id": request_id,
                    "provider": provider_name,
                    "channel_has_settings": isinstance(channel_settings, dict),
                },
            )
            for section_name, section_text in split_prompt_sections(prompt).items():
                log_block(debug_id=debug_id, title=f"PROMPT::{section_name}", value=section_text)
            log_block(
                debug_id=debug_id,
                title="CHANNEL_CONFIG_APPLIED",
                value={
                    "behavior": config.get("behavior"),
                    "identity": config.get("identity"),
                    "tone": config.get("tone"),
                    "rules": config.get("rules"),
                    "objectives_count": len(section_entries(config, "objectives")),
                    "data_collection_count": len(section_entries(config, "data_collection")),
                    "channel_settings": channel_settings if isinstance(channel_settings, dict) else {},
                },
            )

        if should_use_ai(conversation, channel_config):
            try:
                quota_service = QuotaService(db)
                quota_decision = quota_service.can_use_ai(tenant_id=tenant_id)
                if not quota_decision.allowed:
                    quota_message = (
                        channel_settings.get("quota_exceeded_message")
                        if isinstance(channel_settings, dict)
                        else None
                    ) or fallback_message
                    logger.warning(
                        (
                            "AI quota blocked execution "
                            "(conversation_id=%s tenant_id=%s reason=%s remaining_daily_tokens=%s "
                            "remaining_monthly_tokens=%s remaining_daily_requests=%s remaining_monthly_requests=%s)"
                        ),
                        conversation.id,
                        tenant_id,
                        quota_decision.reason,
                        quota_decision.remaining.tokens_daily,
                        quota_decision.remaining.tokens_monthly,
                        quota_decision.remaining.requests_daily,
                        quota_decision.remaining.requests_monthly,
                    )
                    response = quota_message
                else:
                    tool_registry = AIToolRegistryService(db)
                    tool_execution = AIToolExecutionService(db)
                    available_tools, action_map = tool_registry.get_tools(
                        tenant_id=tenant_id,
                        channel_id=channel_id,
                    )
                    logger.info(
                        "AI tools available (conversation_id=%s tenant_id=%s channel_id=%s count=%d)",
                        conversation.id,
                        tenant_id,
                        channel_id,
                        len(available_tools),
                    )
                    tool_names = list(action_map.keys())
                    if debug_enabled and debug_id is not None:
                        log_block(
                            debug_id=debug_id,
                            title="ENABLED_TOOLS",
                            value={
                                "count": len(available_tools),
                                "names": tool_names,
                                "tools": available_tools,
                            },
                        )

                    if available_tools:
                        base_messages = [
                            {"role": "system", "content": prompt},
                            {"role": "system", "content": _SYSTEM_TOOLS_INSTRUCTION},
                            {"role": "user", "content": self._extract_current_user_message(prompt)},
                        ]
                        if debug_enabled and debug_id is not None:
                            log_block(debug_id=debug_id, title="MESSAGES_TO_PROVIDER::INITIAL", value=base_messages)
                        ai_payload = await self.call_ai_chat(
                            prompt=prompt,
                            current_user_message=self._extract_current_user_message(prompt),
                            provider_name=provider_name,
                            tools=available_tools,
                        )
                        response = str((ai_payload or {}).get("response") or "")
                        tool_calls = (ai_payload or {}).get("tool_calls") or []
                        if tool_calls:
                            assistant_message = (ai_payload or {}).get("assistant_message") or {}
                            tool_messages: list[dict[str, Any]] = []
                            total_tool_calls = min(len(tool_calls), MAX_TOOL_CALLS_PER_MESSAGE)
                            for tool_call in tool_calls[:total_tool_calls]:
                                function_payload = tool_call.get("function") or {}
                                action_name = str(function_payload.get("name") or "").strip()
                                action = action_map.get(action_name)
                                arguments = function_payload.get("arguments")
                                if not isinstance(arguments, dict):
                                    arguments = {}

                                logger.info(
                                    "Executing tool call (conversation_id=%s action=%s args_keys=%s)",
                                    conversation.id,
                                    action_name,
                                    list(arguments.keys()),
                                )

                                if action is None:
                                    result_payload = {
                                        "success": False,
                                        "status_code": None,
                                        "error": "tool_not_available_for_channel",
                                    }
                                else:
                                    result_payload = await tool_execution.execute_tool_call(
                                        tenant_id=tenant_id,
                                        action=action,
                                        arguments=arguments,
                                    )
                                tool_messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_call.get("id"),
                                        "name": action_name,
                                        "content": json.dumps(result_payload, ensure_ascii=False),
                                    }
                                )
                                logger.info(
                                    "Tool result ready (conversation_id=%s action=%s success=%s)",
                                    conversation.id,
                                    action_name,
                                    result_payload.get("success"),
                                )
                                if debug_enabled and debug_id is not None:
                                    log_block(
                                        debug_id=debug_id,
                                        title=f"TOOL_RESULT::{action_name}",
                                        value=result_payload,
                                    )

                            if _MAX_TOOL_LOOP_ITERATIONS > 0:
                                follow_up_messages = [
                                    {"role": "system", "content": prompt},
                                    {"role": "system", "content": _SYSTEM_TOOLS_INSTRUCTION},
                                    {"role": "user", "content": self._extract_current_user_message(prompt)},
                                    {
                                        "role": "assistant",
                                        "content": assistant_message.get("content"),
                                        "tool_calls": assistant_message.get("tool_calls"),
                                    },
                                    *tool_messages,
                                ]
                                if debug_enabled and debug_id is not None:
                                    log_block(
                                        debug_id=debug_id,
                                        title="MESSAGES_TO_PROVIDER::FOLLOW_UP",
                                        value=follow_up_messages,
                                    )
                                ai_payload = await AIService(provider_name=provider_name).generate_chat_with_metadata(
                                    follow_up_messages,
                                    tools=available_tools,
                                )
                                response = str((ai_payload or {}).get("response") or "")
                    else:
                        if debug_enabled and debug_id is not None:
                            log_block(
                                debug_id=debug_id,
                                title="MESSAGES_TO_PROVIDER::PROMPT_ONLY",
                                value={"prompt": prompt},
                            )
                        ai_payload = await self.call_ai(prompt, provider_name=provider_name)
                        response = str((ai_payload or {}).get("response") or "")
            except Exception:
                db.rollback()
                logger.exception("AI generation failed for conversation: %s", conversation.id)
        else:
            logger.info("AI gate blocked execution for conversation: %s", conversation.id)

        self._log_interaction(
            db,
            tenant_id=tenant_id,
            channel_id=channel_id,
            contact_id=contact_id,
            conversation_id=conversation.id,
            request_id=request_id,
            prompt=prompt,
            response=response,
            provider=provider_name,
            model=(ai_payload or {}).get("model") or settings.OLLAMA_MODEL,
        )
        self._record_token_usage(
            db,
            tenant_id=tenant_id,
            channel_id=channel_id,
            contact_id=contact_id,
            ai_payload=ai_payload,
            fallback_model=settings.OLLAMA_MODEL,
            provider=provider_name,
            conversation_id=conversation.id,
            message_id=message_id,
            request_id=request_id,
        )
        if debug_enabled and debug_id is not None:
            log_block(
                debug_id=debug_id,
                title="AI_RESPONSE",
                value={
                    "response": response,
                    "tool_calls": (ai_payload or {}).get("tool_calls") or [],
                    "finish_reason": (ai_payload or {}).get("finish_reason"),
                    "usage": {
                        "prompt_eval_count": (ai_payload or {}).get("prompt_eval_count"),
                        "eval_count": (ai_payload or {}).get("eval_count"),
                    },
                    "model": (ai_payload or {}).get("model") or settings.OLLAMA_MODEL,
                    "provider": provider_name,
                },
            )
            log_footer(debug_id=debug_id)

        if not response or not response.strip():
            logger.warning("Empty AI response for conversation: %s - using fallback", conversation.id)
            response = fallback_message
        elif is_out_of_scope(response):
            unsupported = (
                channel_settings.get("unsupported_content_message")
                if isinstance(channel_settings, dict)
                else None
            ) or "No puedo ayudarte con eso."
            logger.warning("Out-of-scope response for conversation: %s", conversation.id)
            response = unsupported

        bot_message_count: Optional[int] = None
        if contact_id is not None:
            try:
                bot_message_count = message_service.increment_contact_usage(
                    db,
                    contact_id=contact_id,
                    conversation_id=conversation.id,
                )
            except Exception:
                logger.exception("Failed to increment bot_message_count for conversation: %s", conversation.id)

        max_messages = 999
        limit_message = None
        if isinstance(channel_settings, dict):
            max_messages = channel_settings.get("max_bot_messages", 999)
            limit_message = channel_settings.get("max_bot_messages_message")

        if bot_message_count is not None and bot_message_count >= max_messages:
            logger.warning(
                "Bot message limit (%d) reached for conversation: %s - switching to human mode",
                max_messages, conversation.id,
            )
            response = limit_message or fallback_message
            try:
                disable_ai(db, conversation)
            except Exception:
                logger.exception("Failed to set human mode for conversation: %s", conversation.id)

        self._apply_user_type_on_completion(db, contact_id, config)

        logger.info("Response ready for conversation: %s", conversation.id)
        return response

    @staticmethod
    def _extract_current_user_message(prompt: str) -> str:
        marker = "[MENSAJE ACTUAL]"
        idx = prompt.rfind(marker)
        if idx < 0:
            return prompt
        segment = prompt[idx:]
        user_marker = "Usuario:"
        user_idx = segment.find(user_marker)
        if user_idx < 0:
            return segment.replace(marker, "").strip()
        return segment[user_idx + len(user_marker):].strip()

    def _record_token_usage(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
        contact_id: Optional[uuid.UUID],
        ai_payload: Optional[dict[str, Any]],
        fallback_model: Optional[str],
        provider: str,
        conversation_id: uuid.UUID,
        message_id: Optional[uuid.UUID],
        request_id: Optional[str],
    ) -> None:
        if not ai_payload:
            logger.debug("No AI payload available to record token usage (conversation_id=%s)", conversation_id)
            return

        def _to_int(value: Any) -> int:
            try:
                return int(value) if value is not None else 0
            except (TypeError, ValueError):
                return 0

        input_tokens = _to_int(ai_payload.get("prompt_eval_count"))
        output_tokens = _to_int(ai_payload.get("eval_count"))
        if input_tokens + output_tokens <= 0:
            logger.warning(
                "AI response without token counters; skipping token usage record (conversation_id=%s)",
                conversation_id,
            )
            return

        model_name = str(ai_payload.get("model") or fallback_model or "unknown")

        try:
            usage_service = UsageService(db)
            usage_event = usage_service.record_usage_event(
                tenant_id=tenant_id,
                channel_id=channel_id,
                conversation_id=conversation_id,
                contact_id=contact_id,
                message_id=message_id,
                request_id=request_id,
                provider=str(provider or "unknown"),
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            if usage_event is None:
                logger.warning(
                    "AI usage event not recorded due to empty counters (conversation_id=%s)",
                    conversation_id,
                )
                return
            logger.info(
                "AI usage event recorded (conversation_id=%s, tenant_id=%s, channel_id=%s, total_tokens=%d)",
                conversation_id,
                tenant_id,
                channel_id,
                usage_event.total_tokens,
            )
        except Exception:
            db.rollback()
            logger.exception(
                "Failed to record token usage (conversation_id=%s, tenant_id=%s)",
                conversation_id,
                tenant_id,
            )

    def _log_interaction(
        self,
        db: Session,
        *,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
        contact_id: Optional[uuid.UUID],
        conversation_id: uuid.UUID,
        request_id: Optional[str],
        prompt: str,
        response: Optional[str],
        provider: str,
        model: str,
    ) -> None:
        try:
            repository = AILogRepository(db)
            repository.create_log({
                "tenant_id": tenant_id,
                "channel_id": channel_id,
                "contact_id": contact_id,
                "conversation_id": conversation_id,
                "request_id": request_id,
                "prompt": prompt,
                "response": response,
                "provider": provider,
                "model": model,
            })
        except Exception:
            db.rollback()
            logger.exception("Failed to save AI log for conversation: %s", conversation_id)

    def _ensure_contact_default_type(
        self,
        db: Session,
        *,
        contact_id: Optional[uuid.UUID],
        config: dict,
        user_types: dict[str, Any],
    ) -> None:
        if not contact_id:
            return

        contact = message_service.get_contact(db, contact_id)
        if not contact or contact.current_type is not None:
            return

        default_type = user_types.get("default_type") if isinstance(user_types, dict) else None
        if not isinstance(default_type, str) or not default_type.strip():
            default_type = config.get("default_type") if isinstance(config.get("default_type"), str) else "new"
        try:
            message_service.ensure_contact_current_type(db, contact.id, default_type)
            logger.info("Assigned initial current_type '%s' to contact: %s", default_type, contact.id)
        except Exception:
            db.rollback()
            logger.exception("Failed to set initial current_type for contact: %s", contact.id)

    def _apply_user_type_on_completion(
        self,
        db: Session,
        contact_id: Optional[uuid.UUID],
        config: dict,
    ) -> None:
        if not contact_id:
            return

        objectives = section_entries(config, "objectives")
        on_completion = None
        for objective in objectives:
            maybe_value = objective.get("on_completion")
            if isinstance(maybe_value, str) and maybe_value.strip():
                on_completion = maybe_value.strip()
                break
        if not on_completion:
            return

        contact = message_service.get_contact(db, contact_id)
        if not contact:
            return

        try:
            message_service.apply_contact_current_type(db, contact.id, on_completion)
            logger.info("Updated current_type to '%s' for contact: %s", on_completion, contact.id)
        except Exception:
            db.rollback()
            logger.exception("Failed to update current_type for contact: %s", contact.id)
