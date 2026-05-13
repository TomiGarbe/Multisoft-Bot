from __future__ import annotations

from app.core.config import settings
from app.models.conversation import MessageAttachment


class MediaProcessingSecurityService:
    def validate_for_processing(self, attachment: MessageAttachment) -> tuple[bool, str | None]:
        if not attachment.mime_type:
            return False, "missing_mime_type"
        allowed = set(settings.attachment_allowed_mime_types_list)
        if attachment.mime_type.split(";")[0].strip().lower() not in allowed:
            return False, "mime_not_allowed_for_processing"
        if attachment.size_bytes is not None and attachment.size_bytes <= 0:
            return False, "invalid_size"
        return True, None
