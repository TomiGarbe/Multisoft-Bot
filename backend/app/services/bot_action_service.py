from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.bot_action import BotAction
from app.models.user import User
from app.repositories.bot_action_repository import BotActionRepository
from app.repositories.channel_bot_action_link_repository import ChannelBotActionLinkRepository
from app.schemas.bot_action import (
    BotActionCreate,
    BotActionEnabledUpdate,
    BotActionListResponse,
    BotActionResponse,
    BotActionUpdate,
)
from app.utils.bot_actions_constants import MAX_RETRY_COUNT, MAX_TIMEOUT_MS
from app.utils.bot_actions_sanitization import sanitize_auth_config, sanitize_mapping_secrets
from app.utils.bot_actions_validators import (
    normalize_tool_name_or_raise,
    validate_auth_config_or_raise,
    validate_external_url_or_raise,
    validate_placeholders_in_action_parts_or_raise,
    validate_response_config_or_raise,
    validate_variable_schemas_or_raise,
)


class BotActionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BotActionRepository(db)
        self.link_repository = ChannelBotActionLinkRepository(db)

    def create_action(self, tenant_id: uuid.UUID, user_id: uuid.UUID, payload: BotActionCreate) -> BotActionResponse:
        normalized_name = self._validate_unique_name(tenant_id=tenant_id, raw_name=payload.name)
        validated_data = self._validated_payload(payload.model_dump())

        action = BotAction(
            tenant_id=tenant_id,
            name=normalized_name,
            description=payload.description,
            enabled=payload.enabled,
            trigger_prompt=payload.trigger_prompt,
            ai_instructions=payload.ai_instructions,
            method=payload.method,
            url=validated_data["url"],
            headers_jsonb=validated_data["headers_jsonb"],
            query_params_jsonb=validated_data["query_params_jsonb"],
            body_jsonb=validated_data["body_jsonb"],
            variables_jsonb=validated_data["variables_jsonb"],
            auth_jsonb=validated_data["auth_jsonb"],
            response_config_jsonb=validated_data["response_config_jsonb"],
            timeout_ms=validated_data["timeout_ms"],
            retry_count=validated_data["retry_count"],
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )

        try:
            self.repository.create(action)
            self.repository.commit()
            self.repository.refresh(action)
            return self._to_response(action)
        except IntegrityError:
            self.repository.rollback()
            raise ValueError("duplicate_action_name")
        except Exception:
            self.repository.rollback()
            raise

    def update_action(
        self,
        tenant_id: uuid.UUID,
        action_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: BotActionUpdate,
    ) -> BotActionResponse:
        action = self._get_action_or_raise(tenant_id, action_id)

        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            normalized_name = self._validate_unique_name(tenant_id=tenant_id, raw_name=data["name"], action_id=action.id)
            action.name = normalized_name

        merged_data = {
            "url": data.get("url", action.url),
            "headers_jsonb": data.get("headers_jsonb", action.headers_jsonb),
            "query_params_jsonb": data.get("query_params_jsonb", action.query_params_jsonb),
            "body_jsonb": data.get("body_jsonb", action.body_jsonb),
            "variables_jsonb": data.get("variables_jsonb", action.variables_jsonb or []),
            "auth_jsonb": data.get("auth_jsonb", action.auth_jsonb),
            "response_config_jsonb": data.get("response_config_jsonb", action.response_config_jsonb),
            "timeout_ms": data.get("timeout_ms", action.timeout_ms),
            "retry_count": data.get("retry_count", action.retry_count),
        }
        validated_data = self._validated_payload(merged_data)

        for field in (
            "description",
            "enabled",
            "trigger_prompt",
            "ai_instructions",
            "method",
        ):
            if field in data:
                setattr(action, field, data[field])

        action.url = validated_data["url"]
        action.headers_jsonb = validated_data["headers_jsonb"]
        action.query_params_jsonb = validated_data["query_params_jsonb"]
        action.body_jsonb = validated_data["body_jsonb"]
        action.variables_jsonb = validated_data["variables_jsonb"]
        action.auth_jsonb = validated_data["auth_jsonb"]
        action.response_config_jsonb = validated_data["response_config_jsonb"]
        action.timeout_ms = validated_data["timeout_ms"]
        action.retry_count = validated_data["retry_count"]
        action.updated_by_user_id = user_id

        try:
            self.repository.update(action)
            self.repository.commit()
            self.repository.refresh(action)
            return self._to_response(action)
        except IntegrityError:
            self.repository.rollback()
            raise ValueError("duplicate_action_name")
        except Exception:
            self.repository.rollback()
            raise

    def delete_action(self, tenant_id: uuid.UUID, action_id: uuid.UUID) -> None:
        action = self._get_action_or_raise(tenant_id, action_id)
        try:
            self.repository.delete(action)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise

    def get_action(self, tenant_id: uuid.UUID, action_id: uuid.UUID) -> BotActionResponse:
        action = self._get_action_or_raise(tenant_id, action_id)
        return self._to_response(action)

    def list_actions(
        self,
        tenant_id: uuid.UUID,
        *,
        enabled: bool | None = None,
        search: str | None = None,
        channel_id: uuid.UUID | None = None,
    ) -> list[BotActionListResponse]:
        actions = self.repository.get_by_tenant(
            tenant_id=tenant_id,
            enabled=enabled,
            search=search,
            channel_id=channel_id,
        )
        return [BotActionListResponse.model_validate(action) for action in actions]

    def set_enabled(
        self,
        tenant_id: uuid.UUID,
        action_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: BotActionEnabledUpdate,
    ) -> BotActionResponse:
        action = self._get_action_or_raise(tenant_id, action_id)
        action.enabled = payload.enabled
        action.updated_by_user_id = user_id
        try:
            self.repository.commit()
            self.repository.refresh(action)
            return self._to_response(action)
        except Exception:
            self.repository.rollback()
            raise

    def get_channel_actions(self, tenant_id: uuid.UUID, channel_bot_config_id: uuid.UUID) -> list[BotActionListResponse]:
        channel_config = self.link_repository.get_channel_bot_config(channel_bot_config_id, tenant_id)
        if channel_config is None:
            raise LookupError("cross_tenant_access")
        actions = self.link_repository.get_channel_actions(channel_bot_config_id)
        return [BotActionListResponse.model_validate(action) for action in actions if action.tenant_id == tenant_id]

    def replace_channel_actions(
        self,
        tenant_id: uuid.UUID,
        channel_bot_config_id: uuid.UUID,
        action_ids: list[uuid.UUID],
    ) -> list[BotActionListResponse]:
        channel_config = self.link_repository.get_channel_bot_config(channel_bot_config_id, tenant_id)
        if channel_config is None:
            raise LookupError("cross_tenant_access")

        unique_action_ids = list(dict.fromkeys(action_ids))
        for action_id in unique_action_ids:
            self._get_action_or_raise(tenant_id, action_id)

        try:
            self.link_repository.replace_channel_actions(
                channel_bot_config_id=channel_bot_config_id,
                action_ids=unique_action_ids,
            )
            self.link_repository.commit()
        except Exception:
            self.link_repository.rollback()
            raise

        return self.get_channel_actions(tenant_id, channel_bot_config_id)

    def _validated_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            validated_variables = validate_variable_schemas_or_raise(data.get("variables_jsonb") or [])
        except ValueError:
            raise ValueError("invalid_placeholder")

        variable_names = [item.name for item in validated_variables]

        try:
            validated_url = validate_external_url_or_raise(data["url"])
        except ValueError:
            raise ValueError("forbidden_url")

        headers_jsonb = data.get("headers_jsonb") or None
        query_params_jsonb = data.get("query_params_jsonb") or None
        body_jsonb = data.get("body_jsonb")

        if headers_jsonb is not None and not isinstance(headers_jsonb, dict):
            raise ValueError("invalid_placeholder")
        if query_params_jsonb is not None and not isinstance(query_params_jsonb, dict):
            raise ValueError("invalid_placeholder")

        headers_as_str = {k: str(v) for k, v in (headers_jsonb or {}).items()}
        query_as_str = {k: str(v) for k, v in (query_params_jsonb or {}).items()}

        body_as_str: str | None
        if isinstance(body_jsonb, str):
            body_as_str = body_jsonb
        elif body_jsonb is None:
            body_as_str = None
        else:
            body_as_str = json.dumps(body_jsonb, ensure_ascii=True)

        try:
            validate_placeholders_in_action_parts_or_raise(
                url=validated_url,
                headers=headers_as_str,
                query_params=query_as_str,
                body=body_as_str,
                allowed_variables=variable_names,
            )
        except ValueError:
            raise ValueError("invalid_placeholder")

        try:
            validated_auth = validate_auth_config_or_raise(data.get("auth_jsonb"))
        except ValueError:
            raise ValueError("invalid_auth_config")

        try:
            validated_response = validate_response_config_or_raise(data.get("response_config_jsonb"))
        except ValueError:
            raise ValueError("invalid_response_config")

        timeout_ms = data.get("timeout_ms")
        if timeout_ms is not None and (timeout_ms <= 0 or timeout_ms > MAX_TIMEOUT_MS):
            raise ValueError("invalid_timeout")

        retry_count = data.get("retry_count")
        if retry_count is not None and (retry_count < 0 or retry_count > MAX_RETRY_COUNT):
            raise ValueError("invalid_retry_count")

        return {
            "url": validated_url,
            "headers_jsonb": headers_as_str or None,
            "query_params_jsonb": query_as_str or None,
            "body_jsonb": body_jsonb,
            "variables_jsonb": [item.model_dump(mode="json") for item in validated_variables],
            "auth_jsonb": validated_auth.model_dump(mode="json"),
            "response_config_jsonb": validated_response.model_dump(mode="json"),
            "timeout_ms": timeout_ms,
            "retry_count": retry_count,
        }

    def _validate_unique_name(
        self,
        *,
        tenant_id: uuid.UUID,
        raw_name: str,
        action_id: uuid.UUID | None = None,
    ) -> str:
        try:
            normalized_name = normalize_tool_name_or_raise(raw_name)
        except ValueError:
            raise ValueError("invalid_tool_name")

        existing = self.repository.get_by_name(tenant_id, normalized_name)
        if existing and existing.id != action_id:
            raise ValueError("duplicate_action_name")
        return normalized_name

    def _get_action_or_raise(self, tenant_id: uuid.UUID, action_id: uuid.UUID) -> BotAction:
        action = self.repository.get_by_id(action_id=action_id, tenant_id=tenant_id)
        if action is None:
            raise LookupError("action_not_found")
        return action

    @staticmethod
    def _to_response(action: BotAction) -> BotActionResponse:
        return BotActionResponse(
            id=action.id,
            tenant_id=action.tenant_id,
            name=action.name,
            description=action.description,
            enabled=action.enabled,
            trigger_prompt=action.trigger_prompt,
            ai_instructions=action.ai_instructions,
            method=action.method,
            url=action.url,
            headers_jsonb=sanitize_mapping_secrets(action.headers_jsonb),
            query_params_jsonb=action.query_params_jsonb,
            body_jsonb=action.body_jsonb,
            variables_jsonb=action.variables_jsonb or [],
            auth_jsonb=sanitize_auth_config(action.auth_jsonb) or {},
            response_config_jsonb=action.response_config_jsonb,
            timeout_ms=action.timeout_ms,
            retry_count=action.retry_count,
            created_by_user_id=action.created_by_user_id,
            updated_by_user_id=action.updated_by_user_id,
            created_at=action.created_at,
            updated_at=action.updated_at,
        )
