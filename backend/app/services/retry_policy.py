from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    initial_backoff_seconds: float
    max_backoff_seconds: float
    backoff_multiplier: float = 2.0
    jitter_ratio: float = 0.1

    def backoff_for_attempt(self, attempt_number: int) -> float:
        base = self.initial_backoff_seconds * (self.backoff_multiplier ** max(0, attempt_number - 1))
        bounded = min(base, self.max_backoff_seconds)
        jitter = bounded * self.jitter_ratio * random.random()
        return bounded + jitter


def run_with_retries(
    *,
    operation_name: str,
    operation: Callable[[], T],
    policy: RetryPolicy,
    is_retryable: Callable[[Exception], bool],
    context: dict[str, object] | None = None,
) -> T:
    ctx = context or {}
    last_error: Exception | None = None
    attempts = max(1, policy.max_attempts)
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            retryable = is_retryable(exc)
            if attempt >= attempts or not retryable:
                logger.warning(
                    "retry_exhausted operation=%s attempt=%s max_attempts=%s retryable=%s ts=%s error=%s context=%s",
                    operation_name,
                    attempt,
                    attempts,
                    retryable,
                    datetime.now(timezone.utc).isoformat(),
                    exc,
                    ctx,
                )
                raise
            backoff = policy.backoff_for_attempt(attempt)
            logger.info(
                "retry_scheduled operation=%s attempt=%s max_attempts=%s backoff_seconds=%.3f ts=%s context=%s",
                operation_name,
                attempt,
                attempts,
                backoff,
                datetime.now(timezone.utc).isoformat(),
                ctx,
            )
            time.sleep(backoff)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"retry_policy_failed_without_error operation={operation_name}")

