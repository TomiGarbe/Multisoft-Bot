from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    FILE = "file"
    MEDIA = "media"
    UNKNOWN = "unknown"


class AttachmentType(str, Enum):
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    FILE = "file"


class StorageBackend(str, Enum):
    NONE = "none"
    PROVIDER = "provider"
    EXTERNAL_URL = "external_url"
    BASE64 = "base64"
    DB = "db"
    S3 = "s3"
    MINIO = "minio"


class AttachmentDownloadStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    DOWNLOADED = "downloaded"
    FAILED = "failed"


class MediaProcessingCapability(str, Enum):
    TRANSCRIPTION = "transcription"
    OCR = "ocr"
    METADATA_EXTRACTION = "metadata_extraction"
    EMBEDDINGS = "embeddings"
    MODERATION = "moderation"
    THUMBNAILS = "thumbnails"
    VISION = "vision"
    DOCUMENT_EXTRACTION = "document_extraction"


class MediaProcessingStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ProcessedArtifactStorageBackend(str, Enum):
    INLINE_JSON = "inline_json"
    DB = "db"
    S3 = "s3"
    MINIO = "minio"
    CDN = "cdn"
