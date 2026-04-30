from datetime import datetime, timezone

from app.schemas.internal.normalized_message import NormalizedMessage
from app.services.message_service import ensure_message_id


def normalize(channel_id: str, payload: dict) -> NormalizedMessage:
    normalized = NormalizedMessage(
        channel_id=channel_id,
        external_message_id=payload.get("id", ""),
        sender_external_id=payload.get("from"),
        sender_name=payload.get("sender_name"),
        content=payload.get("text") or payload.get("body"),
        message_type=payload.get("type", "text"),
        is_group=bool(payload.get("is_group", False)),
        group_id=payload.get("group_id"),
        is_status=bool(payload.get("is_status", False)),
        is_bot=bool(payload.get("is_bot", False)) or payload.get("from_me") is True,
        has_media=bool(payload.get("has_media", False)),
        media_url=payload.get("media_url"),
        timestamp=datetime.now(timezone.utc),
        raw_payload=payload,
    )
    ensure_message_id(normalized)
    return normalized
