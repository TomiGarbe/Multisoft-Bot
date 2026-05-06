from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.ai_usage_repository import AIUsageRepository
from app.repositories import tenant_repository
from app.schemas.quota import QuotaCheckResult, RemainingQuota


class QuotaService:
    """
    Tenant-scoped quota enforcement service.
    Uses ai_usage_events as source of truth for consumption.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.usage_repository = AIUsageRepository(db)

    def can_use_ai(self, *, tenant_id: uuid.UUID) -> QuotaCheckResult:
        limits = self._get_tenant_quota_limits(tenant_id=tenant_id)
        if not limits:
            return QuotaCheckResult(
                allowed=True,
                reason=None,
                remaining=RemainingQuota(),
            )

        day_start, day_end = self._current_day_bounds_utc()
        month_start, month_end = self._current_month_bounds_utc()

        daily_usage = self.usage_repository.get_totals(
            tenant_id=tenant_id,
            start_date=day_start,
            end_date=day_end,
        )
        monthly_usage = self.usage_repository.get_totals(
            tenant_id=tenant_id,
            start_date=month_start,
            end_date=month_end,
        )

        max_daily_tokens = self._to_non_negative_int(limits.get("max_daily_tokens"))
        max_monthly_tokens = self._to_non_negative_int(limits.get("max_monthly_tokens"))
        max_daily_requests = self._to_non_negative_int(limits.get("max_daily_ai_requests"))
        max_monthly_requests = self._to_non_negative_int(limits.get("max_monthly_ai_requests"))

        remaining_tokens_daily = self._remaining(max_daily_tokens, daily_usage["total_tokens"])
        remaining_tokens_monthly = self._remaining(max_monthly_tokens, monthly_usage["total_tokens"])
        remaining_requests_daily = self._remaining(max_daily_requests, daily_usage["request_count"])
        remaining_requests_monthly = self._remaining(max_monthly_requests, monthly_usage["request_count"])
        remaining = RemainingQuota(
            tokens_daily=remaining_tokens_daily,
            tokens_monthly=remaining_tokens_monthly,
            requests_daily=remaining_requests_daily,
            requests_monthly=remaining_requests_monthly,
        )

        if max_daily_tokens is not None and daily_usage["total_tokens"] >= max_daily_tokens:
            return QuotaCheckResult(
                allowed=False,
                reason="daily_token_quota_exceeded",
                remaining=remaining,
            )
        if max_monthly_tokens is not None and monthly_usage["total_tokens"] >= max_monthly_tokens:
            return QuotaCheckResult(
                allowed=False,
                reason="monthly_token_quota_exceeded",
                remaining=remaining,
            )
        if max_daily_requests is not None and daily_usage["request_count"] >= max_daily_requests:
            return QuotaCheckResult(
                allowed=False,
                reason="daily_request_quota_exceeded",
                remaining=remaining,
            )
        if max_monthly_requests is not None and monthly_usage["request_count"] >= max_monthly_requests:
            return QuotaCheckResult(
                allowed=False,
                reason="monthly_request_quota_exceeded",
                remaining=remaining,
            )

        return QuotaCheckResult(
            allowed=True,
            reason=None,
            remaining=remaining,
        )

    def _get_tenant_quota_limits(self, *, tenant_id: uuid.UUID) -> dict[str, Any]:
        tenant = tenant_repository.get_by_id(self.db, tenant_id)
        if tenant is None or not isinstance(tenant.features_jsonb, dict):
            return {}
        quotas = tenant.features_jsonb.get("quotas")
        if not isinstance(quotas, dict):
            return {}
        return quotas

    @staticmethod
    def _to_non_negative_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        if parsed < 0:
            return None
        return parsed

    @staticmethod
    def _remaining(limit: int | None, used: int) -> int | None:
        if limit is None:
            return None
        return max(0, int(limit) - int(used))

    @staticmethod
    def _current_day_bounds_utc() -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    @staticmethod
    def _current_month_bounds_utc() -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            next_month_start = now.replace(
                year=now.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            next_month_start = now.replace(
                month=now.month + 1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        end = next_month_start.replace(microsecond=0) - timedelta(microseconds=1)
        return start, end
