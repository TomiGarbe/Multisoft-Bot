from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.schemas.attachment import AttachmentDTO, AttachmentDownloadStatusDTO, MultimediaMessageDTO
from app.services.attachment_service import AttachmentService
from app.services.multimedia_service import MultimediaService

router = APIRouter(tags=["attachments"])


def _service(db: Session) -> MultimediaService:
    return MultimediaService(AttachmentService(db))


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

    return StreamingResponse(
        iter([blob.content]),
        media_type=blob.descriptor.mime_type,
        status_code=status.HTTP_206_PARTIAL_CONTENT if blob.descriptor.is_partial else status.HTTP_200_OK,
        headers=headers,
    )
