from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass

from app.db.session import SessionLocal
from app.services.attachments.media_processing_job_runner import MediaProcessingJobRunner

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MediaProcessingJobDispatch:
    job_id: uuid.UUID
    tenant_id: uuid.UUID


class MediaProcessingDispatcher:
    def __init__(self, *, max_concurrency: int = 8) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._tasks: set[asyncio.Task[None]] = set()

    def enqueue(self, job: MediaProcessingJobDispatch) -> None:
        logger.warning(
            "[MULTIMEDIA][PROCESSING] enqueue job_id=%s tenant_id=%s",
            job.job_id,
            job.tenant_id,
        )
        task = asyncio.create_task(self._run_job(job))
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)

    async def _run_job(self, job: MediaProcessingJobDispatch) -> None:
        async with self._semaphore:
            db = SessionLocal()
            try:
                logger.warning(
                    "[MULTIMEDIA][PROCESSING] worker_start job_id=%s tenant_id=%s",
                    job.job_id,
                    job.tenant_id,
                )
                MediaProcessingJobRunner(db).run(job_id=job.job_id, tenant_id=job.tenant_id)
                logger.warning(
                    "[MULTIMEDIA][PROCESSING] worker_done job_id=%s tenant_id=%s",
                    job.job_id,
                    job.tenant_id,
                )
            except Exception:
                db.rollback()
                logger.exception("[MULTIMEDIA][PROCESSING] background_failed job_id=%s tenant_id=%s", job.job_id, job.tenant_id)
            finally:
                db.close()

    def _on_task_done(self, task: asyncio.Task[None]) -> None:
        self._tasks.discard(task)
        try:
            task.result()
        except Exception:
            logger.exception("media_processing_background_unhandled_exception")


media_processing_dispatcher = MediaProcessingDispatcher()
