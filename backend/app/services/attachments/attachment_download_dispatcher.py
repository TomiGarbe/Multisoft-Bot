from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass

from app.db.session import SessionLocal
from app.services.attachments.attachment_downloader import AttachmentDownloader

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AttachmentDownloadJob:
    attachment_id: uuid.UUID
    tenant_id: uuid.UUID


class AttachmentDownloadDispatcher:
    def __init__(self, *, max_concurrency: int = 16) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._tasks: set[asyncio.Task[None]] = set()

    def enqueue(self, job: AttachmentDownloadJob) -> None:
        logger.warning(
            "[MULTIMEDIA][DOWNLOAD] enqueue attachment_id=%s tenant_id=%s",
            job.attachment_id,
            job.tenant_id,
        )
        task = asyncio.create_task(self._run_job(job))
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)

    async def _run_job(self, job: AttachmentDownloadJob) -> None:
        async with self._semaphore:
            db = SessionLocal()
            try:
                logger.warning(
                    "[MULTIMEDIA][DOWNLOAD] worker_start attachment_id=%s tenant_id=%s",
                    job.attachment_id,
                    job.tenant_id,
                )
                AttachmentDownloader(db).process_attachment(
                    attachment_id=job.attachment_id,
                    tenant_id=job.tenant_id,
                )
                logger.warning(
                    "[MULTIMEDIA][DOWNLOAD] worker_done attachment_id=%s tenant_id=%s",
                    job.attachment_id,
                    job.tenant_id,
                )
            except Exception:
                db.rollback()
                logger.exception(
                    "attachment_download_background_failed attachment_id=%s tenant_id=%s",
                    job.attachment_id,
                    job.tenant_id,
                )
            finally:
                db.close()

    def _on_task_done(self, task: asyncio.Task[None]) -> None:
        self._tasks.discard(task)
        try:
            task.result()
        except Exception:
            logger.exception("attachment_download_background_unhandled_exception")


attachment_download_dispatcher = AttachmentDownloadDispatcher()
