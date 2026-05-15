from __future__ import annotations

import base64
import binascii
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant
from app.api.dependencies.permissions import require_permission
from app.core.config import settings
from app.db.session import get_db
from app.schemas.attachment import AttachmentDTO, AttachmentDownloadStatusDTO, MultimediaMessageDTO
from app.schemas.internal.message_enums import AttachmentType
from app.services.attachment_service import AttachmentService
from app.services.multimedia_service import MultimediaService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["attachments"])


def _service(db: Session) -> MultimediaService:
    return MultimediaService(AttachmentService(db))


def _get_max_size_bytes(attachment_type: AttachmentType) -> int:
    if attachment_type == AttachmentType.IMAGE:
        return settings.ATTACHMENT_MAX_IMAGE_BYTES
    if attachment_type == AttachmentType.AUDIO:
        return settings.ATTACHMENT_MAX_AUDIO_BYTES
    if attachment_type == AttachmentType.VIDEO:
        return settings.ATTACHMENT_MAX_VIDEO_BYTES
    return settings.ATTACHMENT_MAX_DOCUMENT_BYTES


@router.post("/upload")
async def upload_attachment(
    request: Request,
    file: UploadFile = File(...),
    attachment_type: AttachmentType = Form(...),
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.send")),
):
    logger.warning(
        "[MULTIMEDIA][UPLOAD] upload_start tenant_id=%s filename=%s attachment_type=%s content_type=%s has_auth=%s has_tenant_header=%s",
        current_tenant_id,
        file.filename,
        attachment_type.value,
        request.headers.get("content-type"),
        bool(request.headers.get("authorization")),
        bool(request.headers.get("x-tenant-id")),
    )
    payload = await file.read()
    size_bytes = len(payload)
    mime_type = (file.content_type or "application/octet-stream").split(";")[0].strip().lower()
    allowed_mimes = set(settings.attachment_allowed_mime_types_list)
    if mime_type not in allowed_mimes:
        logger.warning(
            "[MULTIMEDIA][UPLOAD] upload_error tenant_id=%s reason=mime_not_allowed filename=%s mime=%s size_bytes=%s",
            current_tenant_id,
            file.filename,
            mime_type,
            size_bytes,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachment MIME type is not allowed")

    max_size = _get_max_size_bytes(attachment_type)
    if size_bytes <= 0 or size_bytes > max_size:
        logger.warning(
            "[MULTIMEDIA][UPLOAD] upload_error tenant_id=%s reason=size_invalid filename=%s mime=%s size_bytes=%s max_bytes=%s",
            current_tenant_id,
            file.filename,
            mime_type,
            size_bytes,
            max_size,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachment size is invalid for attachment type")

    try:
        base64_payload = base64.b64encode(payload).decode("ascii")
    except (ValueError, binascii.Error):
        logger.warning(
            "[MULTIMEDIA][UPLOAD] upload_error tenant_id=%s reason=base64_encode_failed filename=%s",
            current_tenant_id,
            file.filename,
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Attachment upload failed")

    provider_media_id = str(uuid.uuid4())
    provider_url = f"data:{mime_type};base64,{base64_payload}"
    logger.warning(
        "[MULTIMEDIA][UPLOAD] upload_completed tenant_id=%s mime=%s size_bytes=%s attachment_id=%s",
        current_tenant_id,
        mime_type,
        size_bytes,
        provider_media_id,
    )
    return {
        "attachment_id": provider_media_id,
        "provider_media_id": provider_media_id,
        "provider_url": provider_url,
        "mime_type": mime_type,
        "filename": file.filename,
        "size_bytes": size_bytes,
    }


@router.get("/{attachment_id}", response_model=AttachmentDTO)
async def get_attachment_metadata(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    item = _service(db).get_attachment(attachment_id=attachment_id, tenant_id=current_tenant_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return item


@router.get("/message/{message_id}", response_model=MultimediaMessageDTO)
async def list_message_attachments(
    message_id: uuid.UUID,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    safe_limit = max(1, min(limit, 500))
    return _service(db).list_attachments_for_message(
        message_id=message_id,
        tenant_id=current_tenant_id,
        offset=max(offset, 0),
        limit=safe_limit,
    )


@router.get("/{attachment_id}/status", response_model=AttachmentDownloadStatusDTO)
async def get_attachment_download_status(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    state = _service(db).get_download_status(attachment_id=attachment_id, tenant_id=current_tenant_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return state


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: uuid.UUID,
    range_header: Optional[str] = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    logger.warning(
        "[MULTIMEDIA][STREAM] download_request attachment_id=%s tenant_id=%s has_range=%s",
        attachment_id,
        current_tenant_id,
        bool(range_header),
    )
    blob = _service(db).get_blob(
        attachment_id=attachment_id,
        tenant_id=current_tenant_id,
        range_header=range_header,
        as_download=True,
    )
    if blob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment blob not found")
    headers = {
        "Content-Disposition": blob.descriptor.content_disposition,
        "Accept-Ranges": "bytes",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, max-age=60",
    }
    if blob.descriptor.is_partial and blob.descriptor.total_size is not None:
        headers["Content-Range"] = (
            f"bytes {blob.descriptor.range_start}-{blob.descriptor.range_end}/{blob.descriptor.total_size}"
        )
    logger.warning(
        "[MULTIMEDIA][STREAM] download_response attachment_id=%s tenant_id=%s mime=%s size_bytes=%s status_code=%s is_partial=%s",
        attachment_id,
        current_tenant_id,
        blob.descriptor.mime_type,
        blob.descriptor.size_bytes,
        status.HTTP_206_PARTIAL_CONTENT if blob.descriptor.is_partial else status.HTTP_200_OK,
        blob.descriptor.is_partial,
    )
    return Response(
        content=blob.content,
        media_type=blob.descriptor.mime_type,
        status_code=status.HTTP_206_PARTIAL_CONTENT if blob.descriptor.is_partial else status.HTTP_200_OK,
        headers=headers,
    )


@router.get("/{attachment_id}/stream")
async def stream_attachment(
    attachment_id: uuid.UUID,
    range_header: Optional[str] = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("messages.read")),
):
    logger.warning(
        "[MULTIMEDIA][STREAM] stream_request attachment_id=%s tenant_id=%s has_range=%s",
        attachment_id,
        current_tenant_id,
        bool(range_header),
    )
    blob = _service(db).get_blob(
        attachment_id=attachment_id,
        tenant_id=current_tenant_id,
        range_header=range_header,
        as_download=False,
    )
    if blob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment blob not found")

    headers = {
        "Content-Disposition": blob.descriptor.content_disposition,
        "Accept-Ranges": "bytes",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, max-age=60",
        "Content-Length": str(blob.descriptor.size_bytes),
    }
    if blob.descriptor.is_partial and blob.descriptor.total_size is not None:
        headers["Content-Range"] = (
            f"bytes {blob.descriptor.range_start}-{blob.descriptor.range_end}/{blob.descriptor.total_size}"
        )

    logger.warning(
        "[MULTIMEDIA][STREAM] stream_response attachment_id=%s tenant_id=%s mime=%s size_bytes=%s status_code=%s is_partial=%s",
        attachment_id,
        current_tenant_id,
        blob.descriptor.mime_type,
        blob.descriptor.size_bytes,
        status.HTTP_206_PARTIAL_CONTENT if blob.descriptor.is_partial else status.HTTP_200_OK,
        blob.descriptor.is_partial,
    )
    return StreamingResponse(
        iter([blob.content]),
        media_type=blob.descriptor.mime_type,
        status_code=status.HTTP_206_PARTIAL_CONTENT if blob.descriptor.is_partial else status.HTTP_200_OK,
        headers=headers,
    )
