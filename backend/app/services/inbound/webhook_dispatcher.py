import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from app.db.session import SessionLocal
from app.services.inbound.webhook_handler import process_webhook_payload

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookJob:
    tenant_id: uuid.UUID
    channel_id: uuid.UUID
    provider_name: str
    payload: dict[str, Any]


class WebhookDispatcher:
    """In-process dispatcher for fire-and-forget webhook processing."""

    def __init__(self, *, max_concurrency: int = 64, task_timeout_seconds: float = 120.0) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._task_timeout_seconds = task_timeout_seconds
        self._tasks: set[asyncio.Task[None]] = set()

    def enqueue(self, job: WebhookJob) -> None:
        task = asyncio.create_task(self._run_job(job))
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)

    async def _run_job(self, job: WebhookJob) -> None:
        async with self._semaphore:
            db = SessionLocal()
            try:
                logger.info(
                    "webhook_background_start tenant_id=%s channel_id=%s provider=%s",
                    job.tenant_id,
                    job.channel_id,
                    job.provider_name,
                )
                await asyncio.wait_for(
                    process_webhook_payload(
                        db=db,
                        channel_id=job.channel_id,
                        payload=job.payload,
                        tenant_id=job.tenant_id,
                        provider_name=job.provider_name,
                    ),
                    timeout=self._task_timeout_seconds,
                )
                logger.info(
                    "webhook_background_done tenant_id=%s channel_id=%s provider=%s",
                    job.tenant_id,
                    job.channel_id,
                    job.provider_name,
                )
            except asyncio.TimeoutError:
                db.rollback()
                logger.exception(
                    "webhook_background_timeout tenant_id=%s channel_id=%s provider=%s timeout=%s",
                    job.tenant_id,
                    job.channel_id,
                    job.provider_name,
                    self._task_timeout_seconds,
                )
            except Exception:
                db.rollback()
                logger.exception(
                    "webhook_background_failed tenant_id=%s channel_id=%s provider=%s",
                    job.tenant_id,
                    job.channel_id,
                    job.provider_name,
                )
            finally:
                db.close()

    def _on_task_done(self, task: asyncio.Task[None]) -> None:
        self._tasks.discard(task)
        try:
            task.result()
        except Exception:
            logger.exception("webhook_background_unhandled_exception")


webhook_dispatcher = WebhookDispatcher()
