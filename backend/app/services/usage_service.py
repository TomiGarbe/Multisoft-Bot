from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.ai.ai_log_repository import AILogRepository
from app.repositories.ai_usage_repository import AIUsageRepository


class UsageService:
    """
    Central usage/analytics service.
    Handles usage events and derived metrics only (no AI orchestration logic).
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.usage_repository = AIUsageRepository(db)
        self.log_repository = AILogRepository(db)

    def record_usage_event(
        self,
        *,
        tenant_id: uuid.UUID,
        channel_id: uuid.UUID,
        conversation_id: uuid.UUID,
        contact_id: uuid.UUID | None,
        message_id: uuid.UUID | None,
        request_id: str | None,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ):
        total_tokens = int(input_tokens) + int(output_tokens)
        if total_tokens <= 0:
            return None
        return self.usage_repository.create_event(
            tenant_id=tenant_id,
            channel_id=channel_id,
            conversation_id=conversation_id,
            contact_id=contact_id,
            message_id=message_id,
            request_id=request_id,
            provider=provider,
            model=model,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            total_tokens=total_tokens,
        )

    def get_tenant_daily_usage(
        self,
        *,
        tenant_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        return self.usage_repository.get_time_series(
            granularity="day",
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_tenant_monthly_usage(
        self,
        *,
        tenant_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        return self.usage_repository.get_time_series(
            granularity="month",
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_channel_daily_usage(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        channel_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        return self.usage_repository.get_time_series(
            granularity="day",
            tenant_id=tenant_id,
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_channel_monthly_usage(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        channel_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        return self.usage_repository.get_time_series(
            granularity="month",
            tenant_id=tenant_id,
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_global_daily_usage(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        return self.usage_repository.get_time_series(
            granularity="day",
            start_date=start_date,
            end_date=end_date,
        )

    def get_global_monthly_usage(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        return self.usage_repository.get_time_series(
            granularity="month",
            start_date=start_date,
            end_date=end_date,
        )

    def get_tenant_totals(
        self,
        *,
        tenant_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        return self.usage_repository.get_totals(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_channel_totals(
        self,
        *,
        channel_id: uuid.UUID,
        tenant_id: uuid.UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        return self.usage_repository.get_totals(
            channel_id=channel_id,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_global_totals(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        return self.usage_repository.get_totals(
            start_date=start_date,
            end_date=end_date,
        )

    def get_request_correlation(self, request_id: str) -> dict[str, Any]:
        usage_event = self.usage_repository.get_event_by_request_id(request_id)
        ai_logs = self.log_repository.get_by_request_id(request_id)
        return {
            "request_id": request_id,
            "usage_event": usage_event,
            "ai_logs": ai_logs,
        }
