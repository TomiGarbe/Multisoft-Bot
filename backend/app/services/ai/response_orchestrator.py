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
import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation
from app.repositories.ai.ai_log_repository import AILogRepository
from app.services.ai.ai_service import AIService
from app.services.ai.provider_routing import AIProviderRoute, resolve_provider_route
from app.services.ai.multimodal_payload_builder import AIMultimodalPayloadBuilder
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
from app.services.attachment_service import AttachmentService

logger = logging.getLogger(__name__)

_DEFAULT_FALLBACK = "No pude procesar tu mensaje en este momento, podes intentar nuevamente?"
_MAX_TOOL_LOOP_ITERATIONS = 1
_SYSTEM_TOOLS_INSTRUCTION = (
    "Si el usuario pide datos externos o en tiempo real, debes usar las tools disponibles antes de responder. "
    "No digas que no tenes acceso si hay tools habilitadas. "
    "No inventes resultados: primero ejecuta la tool y luego responde con el resultado real. "
    "Si una tool falla, explicalo naturalmente en contexto y no hables de media no soportada. "
    "Nunca inventes valores aproximados, estimaciones ni cotizaciones si la tool falla. "
    "Si no hay datos reales de la tool, decilo explicitamente y pedi reintentar. "
    "Prioriza resolver la consulta actual del usuario antes de objetivos comerciales."
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

    async def call_ai(self, prompt: str, route: AIProviderRoute) -> dict[str, Any]:
        normalized_prompt = self._normalize_prompt(prompt)
        logger.info(
            "[AI][PAYLOAD] provider=%s model=%s mode=generate prompt_chars=%s prompt_preview=%s",
            route.provider,
            route.model,
            len(normalized_prompt or ""),
            (normalized_prompt or "")[:180].replace("\n", "\\n"),
        )
        logger.info("[AI][INPUT] mode=generate prompt_chars=%s", len(normalized_prompt or ""))
        ai_service = AIService(route=route)
        started = time.perf_counter()
        payload = await ai_service.generate_with_metadata(normalized_prompt)
        self._log_ai_usage_observability(
            payload=payload,
            provider=route.provider,
            model=route.model,
            duration_ms=int((time.perf_counter() - started) * 1000),
            context_chars=len(normalized_prompt or ""),
            images_included=0,
            included_image_bytes=0,
            approx_payload_bytes=len((normalized_prompt or "").encode("utf-8")),
        )
        return payload

    async def call_ai_chat(
        self,
        *,
        db: Session,
        tenant_id: uuid.UUID,
        message_id: Optional[uuid.UUID],
        prompt: str,
        current_user_message: str,
        route: AIProviderRoute,
        tools: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        ai_service = AIService(route=route)
        user_content, multimodal_stats = AIMultimodalPayloadBuilder(db).build_user_content(
            tenant_id=tenant_id,
            message_id=message_id,
            user_text=current_user_message,
            supports_vision=route.capabilities.supports_vision,
        )
        normalized_prompt = self._normalize_prompt(prompt)
        messages = [
            {"role": "system", "content": normalized_prompt},
            {"role": "system", "content": _SYSTEM_TOOLS_INSTRUCTION},
            {"role": "user", "content": user_content},
        ]
        approx_payload_bytes = len(json.dumps({"model": route.model, "messages": messages}, ensure_ascii=False).encode("utf-8"))
        if approx_payload_bytes > settings.AI_MAX_MULTIMODAL_PAYLOAD_BYTES:
            logger.warning(
                "[AI][MULTIMODAL] payload_limit_exceeded provider=%s model=%s payload_bytes=%s max_bytes=%s",
                route.provider,
                route.model,
                approx_payload_bytes,
                settings.AI_MAX_MULTIMODAL_PAYLOAD_BYTES,
            )
            raise ValueError("multimodal_payload_too_large")
        logger.info(
            "[AI][PAYLOAD] provider=%s model=%s mode=chat messages=%s roles=%s tools_count=%s message_content_types=%s images_included=%s images_skipped=%s vision_supported=%s approx_payload_bytes=%s",
            route.provider,
            route.model,
            len(messages),
            ",".join(str(item.get("role")) for item in messages),
            len(tools or []),
            ",".join(type(item.get("content")).__name__ for item in messages),
            multimodal_stats.get("images_included", 0),
            multimodal_stats.get("images_skipped", 0),
            route.capabilities.supports_vision,
            approx_payload_bytes,
        )
        logger.info(
            "[AI][INPUT] mode=chat user_message_chars=%s images_included=%s vision_supported=%s",
            len(current_user_message or ""),
            multimodal_stats.get("images_included", 0),
            route.capabilities.supports_vision,
        )
        started = time.perf_counter()
        payload = await ai_service.generate_chat_with_metadata(messages, tools=tools)
        self._log_ai_usage_observability(
            payload=payload,
            provider=route.provider,
            model=route.model,
            duration_ms=int((time.perf_counter() - started) * 1000),
            context_chars=len(normalized_prompt or "") + len(current_user_message or ""),
            images_included=int(multimodal_stats.get("images_included", 0)),
            included_image_bytes=int(multimodal_stats.get("included_image_bytes", 0)),
            approx_payload_bytes=approx_payload_bytes,
        )
        return payload

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
        inbound_has_media: bool = False,
    ) -> Optional[str]:
        config = channel_config.config_jsonb or {}
        channel_settings = channel_config.settings_jsonb or {}
        route = resolve_provider_route(channel_settings if isinstance(channel_settings, dict) else None)
        provider_name = route.provider
        if inbound_has_media and not route.capabilities.supports_vision:
            logger.warning(
                "[AI][MULTIMODAL] inbound_media_without_vision conversation_id=%s provider=%s model=%s",
                conversation.id,
                route.provider,
                route.model,
            )
        logger.info(
            "AI route resolved (conversation_id=%s provider=%s model=%s supports_tools=%s supports_vision=%s supports_streaming=%s)",
            conversation.id,
            route.provider,
            route.model,
            route.capabilities.supports_tools,
            route.capabilities.supports_vision,
            route.capabilities.supports_streaming,
        )
        self._log_inbound_media_trace(
            db=db,
            tenant_id=tenant_id,
            message_id=message_id,
            conversation_id=conversation.id,
            route=route,
        )

        behavior = config.get("behavior")
        fallback_message = (
            (behavior.get("fallback_message") if isinstance(behavior, dict) else None)
            or _DEFAULT_FALLBACK
        )

        response = None
        ai_payload: dict[str, Any] | None = None
        tools_available = False
        tool_call_attempted = False
        tool_failure_detected = False

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
                    logger.info(
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
                    tools_available = bool(available_tools)
                    logger.info(
                        "AI tools available (conversation_id=%s tenant_id=%s channel_id=%s count=%d)",
                        conversation.id,
                        tenant_id,
                        channel_id,
                        len(available_tools),
                    )
                    if available_tools and route.capabilities.supports_tools:
                        ai_payload = await self.call_ai_chat(
                            db=db,
                            tenant_id=tenant_id,
                            message_id=message_id,
                            prompt=prompt,
                            current_user_message=self._extract_current_user_message(prompt),
                            route=route,
                            tools=available_tools,
                        )
                        response = str((ai_payload or {}).get("response") or "")
                        tool_calls = (ai_payload or {}).get("tool_calls") or []
                        tool_call_attempted = bool(tool_calls)
                        logger.info(
                            "AI response parsed (conversation_id=%s provider=%s tool_calls=%d finish_reason=%s)",
                            conversation.id,
                            provider_name,
                            len(tool_calls),
                            (ai_payload or {}).get("finish_reason"),
                        )
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
                                if not bool(result_payload.get("success")):
                                    tool_failure_detected = True
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

                            if _MAX_TOOL_LOOP_ITERATIONS > 0:
                                follow_up_user_content, _ = AIMultimodalPayloadBuilder(db).build_user_content(
                                    tenant_id=tenant_id,
                                    message_id=message_id,
                                    user_text=self._extract_current_user_message(prompt),
                                    supports_vision=route.capabilities.supports_vision,
                                )
                                follow_up_messages = [
                                    {"role": "system", "content": prompt},
                                    {"role": "system", "content": _SYSTEM_TOOLS_INSTRUCTION},
                                    {"role": "user", "content": follow_up_user_content},
                                    {
                                        "role": "assistant",
                                        "content": assistant_message.get("content"),
                                        "tool_calls": assistant_message.get("tool_calls"),
                                    },
                                    *tool_messages,
                                ]
                                follow_up_payload_bytes = len(
                                    json.dumps({"model": route.model, "messages": follow_up_messages}, ensure_ascii=False).encode("utf-8")
                                )
                                if follow_up_payload_bytes > settings.AI_MAX_MULTIMODAL_PAYLOAD_BYTES:
                                    raise ValueError("multimodal_payload_too_large")
                                ai_payload = await AIService(route=route).generate_chat_with_metadata(
                                    follow_up_messages,
                                    tools=available_tools,
                                )
                                response = str((ai_payload or {}).get("response") or "")
                                logger.info(
                                    "AI follow up after tools (conversation_id=%s finish_reason=%s tool_calls=%d)",
                                    conversation.id,
                                    (ai_payload or {}).get("finish_reason"),
                                    len((ai_payload or {}).get("tool_calls") or []),
                                )
                        else:
                            logger.info(
                                "AI did not call tools (conversation_id=%s provider=%s tools_available=%d)",
                                conversation.id,
                                provider_name,
                                len(action_map),
                            )
                    elif available_tools and not route.capabilities.supports_tools:
                        logger.warning(
                            "AI provider does not support tools; falling back to prompt-only call (conversation_id=%s provider=%s)",
                            conversation.id,
                            provider_name,
                        )
                        ai_payload = await self.call_ai(prompt, route=route)
                        response = str((ai_payload or {}).get("response") or "")
                    else:
                        logger.info(
                            "AI WITHOUT TOOLS (conversation_id=%s provider=%s reason=no_tools_configured_for_channel)",
                            conversation.id,
                            provider_name,
                        )
                        ai_payload = await self.call_ai(prompt, route=route)
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
            model=(ai_payload or {}).get("model") or route.model,
        )
        self._record_token_usage(
            db,
            tenant_id=tenant_id,
            channel_id=channel_id,
            contact_id=contact_id,
            ai_payload=ai_payload,
            fallback_model=route.model,
            provider=provider_name,
            conversation_id=conversation.id,
            message_id=message_id,
            request_id=request_id,
        )
        if not response or not response.strip():
            if tool_failure_detected:
                tool_failure_message = (
                    channel_settings.get("tool_failure_message")
                    if isinstance(channel_settings, dict)
                    else None
                ) or "No pude obtener esa informacion en este momento. Podes intentar nuevamente en unos minutos."
                logger.warning(
                    "Empty AI response after tool failure for conversation: %s - using tool_failure_message",
                    conversation.id,
                )
                response = tool_failure_message
            else:
                logger.warning("Empty AI response for conversation: %s - using fallback", conversation.id)
                response = fallback_message
        elif is_out_of_scope(response):
            if inbound_has_media:
                unsupported = (
                    channel_settings.get("unsupported_content_message")
                    if isinstance(channel_settings, dict)
                    else None
                ) or "Por el momento no puedo procesar ese tipo de archivo."
                logger.warning("Out-of-scope with inbound media for conversation: %s", conversation.id)
                response = unsupported
            elif tools_available or tool_call_attempted:
                logger.warning(
                    "Out-of-scope detector ignored because tools were available/attempted (conversation_id=%s)",
                    conversation.id,
                )
            else:
                out_of_scope_message = (
                    channel_settings.get("out_of_scope_message")
                    if isinstance(channel_settings, dict)
                    else None
                ) or "No puedo ayudarte con eso."
                logger.warning("Out-of-scope response for conversation: %s", conversation.id)
                response = out_of_scope_message

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

    def _log_inbound_media_trace(
        self,
        *,
        db: Session,
        tenant_id: uuid.UUID,
        message_id: Optional[uuid.UUID],
        conversation_id: uuid.UUID,
        route: AIProviderRoute,
    ) -> None:
        if not message_id:
            logger.warning(
                "[AI][MULTIMEDIA] conversation_id=%s message_id=none attachments=unknown reason=no_message_id",
                conversation_id,
            )
            return
        attachments = AttachmentService(db).list_by_message_id_and_tenant(message_id=message_id, tenant_id=tenant_id)
        model_name = route.model
        supports_multimodal = route.capabilities.supports_vision
        logger.info(
            "[AI][MULTIMEDIA] conversation_id=%s message_id=%s provider=%s model=%s attachments=%s multimodal_supported=%s",
            conversation_id,
            message_id,
            route.provider,
            model_name,
            len(attachments),
            supports_multimodal,
        )
        for attachment in attachments:
            skip_reason = "context_text_only_pipeline"
            if attachment.attachment_type.value == "audio" and not supports_multimodal:
                skip_reason = "model_not_multimodal"
            logger.debug(
                "[AI][MULTIMEDIA] attachment_id=%s type=%s skipped=%s reason=%s",
                attachment.id,
                attachment.attachment_type.value,
                True,
                skip_reason,
            )

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

    @staticmethod
    def _normalize_prompt(prompt: str) -> str:
        value = prompt or ""
        max_chars = max(1000, settings.AI_MAX_PROMPT_CHARS)
        if len(value) <= max_chars:
            return value
        logger.warning(
            "[AI][PAYLOAD] prompt_truncated original_chars=%s max_chars=%s",
            len(value),
            max_chars,
        )
        return value[-max_chars:]

    @staticmethod
    def _log_ai_usage_observability(
        *,
        payload: dict[str, Any] | None,
        provider: str,
        model: str,
        duration_ms: int,
        context_chars: int,
        images_included: int,
        included_image_bytes: int,
        approx_payload_bytes: int,
    ) -> None:
        payload_data = payload or {}
        input_tokens = payload_data.get("prompt_eval_count")
        output_tokens = payload_data.get("eval_count")
        total_tokens = None
        try:
            if input_tokens is not None or output_tokens is not None:
                total_tokens = int(input_tokens or 0) + int(output_tokens or 0)
        except Exception:
            total_tokens = None
        logger.info(
            "[AI][METRICS] provider=%s model=%s duration_ms=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s context_chars=%s images_included=%s included_image_bytes=%s approx_payload_bytes=%s",
            provider,
            model,
            duration_ms,
            input_tokens,
            output_tokens,
            total_tokens,
            context_chars,
            images_included,
            included_image_bytes,
            approx_payload_bytes,
        )

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
                logger.info(
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
