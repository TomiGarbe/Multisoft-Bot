from __future__ import annotations

from app.models.conversation import MessageAttachment
from app.schemas.internal.message_enums import AttachmentType, MediaProcessingCapability


class MediaProcessingCapabilityService:
    def resolve_capabilities(self, attachment: MessageAttachment) -> list[MediaProcessingCapability]:
        by_type: dict[AttachmentType, list[MediaProcessingCapability]] = {
            AttachmentType.AUDIO: [
                MediaProcessingCapability.TRANSCRIPTION,
                MediaProcessingCapability.MODERATION,
                MediaProcessingCapability.EMBEDDINGS,
            ],
            AttachmentType.IMAGE: [
                MediaProcessingCapability.OCR,
                MediaProcessingCapability.VISION,
                MediaProcessingCapability.MODERATION,
                MediaProcessingCapability.THUMBNAILS,
                MediaProcessingCapability.EMBEDDINGS,
            ],
            AttachmentType.DOCUMENT: [
                MediaProcessingCapability.OCR,
                MediaProcessingCapability.DOCUMENT_EXTRACTION,
                MediaProcessingCapability.EMBEDDINGS,
                MediaProcessingCapability.MODERATION,
            ],
            AttachmentType.VIDEO: [
                MediaProcessingCapability.TRANSCRIPTION,
                MediaProcessingCapability.THUMBNAILS,
                MediaProcessingCapability.MODERATION,
            ],
            AttachmentType.FILE: [
                MediaProcessingCapability.METADATA_EXTRACTION,
                MediaProcessingCapability.MODERATION,
            ],
        }
        capabilities = by_type.get(attachment.attachment_type, [MediaProcessingCapability.METADATA_EXTRACTION])
        if MediaProcessingCapability.METADATA_EXTRACTION not in capabilities:
            capabilities = [MediaProcessingCapability.METADATA_EXTRACTION, *capabilities]
        return capabilities
