from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.metrics import AIUsageEvent
from app.repositories.base_repository import BaseRepository


class AIUsageRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create_event(
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
        total_tokens: int,
    ) -> AIUsageEvent:
        event = AIUsageEvent(
            tenant_id=tenant_id,
            channel_id=channel_id,
            conversation_id=conversation_id,
            contact_id=contact_id,
            message_id=message_id,
            request_id=request_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def get_total_tokens_by_tenant(self, tenant_id: uuid.UUID) -> int:
        query = select(func.coalesce(func.sum(AIUsageEvent.total_tokens), 0)).where(
            AIUsageEvent.tenant_id == tenant_id
        )
        return int(self.db.execute(query).scalar_one())

    def get_total_tokens_by_tenant_and_range(
        self,
        *,
        tenant_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        query = select(func.coalesce(func.sum(AIUsageEvent.total_tokens), 0)).where(
            AIUsageEvent.tenant_id == tenant_id,
            AIUsageEvent.created_at >= start_date,
            AIUsageEvent.created_at <= end_date,
        )
        return int(self.db.execute(query).scalar_one())

    def get_totals(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        tenant_id: uuid.UUID | None = None,
        channel_id: uuid.UUID | None = None,
    ) -> dict[str, int]:
        query = select(
            func.count(AIUsageEvent.id),
            func.coalesce(func.sum(AIUsageEvent.input_tokens), 0),
            func.coalesce(func.sum(AIUsageEvent.output_tokens), 0),
            func.coalesce(func.sum(AIUsageEvent.total_tokens), 0),
        )
        query = self._apply_filters(
            query,
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id,
            channel_id=channel_id,
        )
        requests, input_tokens, output_tokens, total_tokens = self.db.execute(query).one()
        return {
            "request_count": int(requests or 0),
            "input_tokens": int(input_tokens or 0),
            "output_tokens": int(output_tokens or 0),
            "total_tokens": int(total_tokens or 0),
        }

    def get_time_series(
        self,
        *,
        granularity: Literal["day", "month"],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        tenant_id: uuid.UUID | None = None,
        channel_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        period = func.date_trunc(granularity, AIUsageEvent.created_at).label("period_start")
        query = select(
            period,
            func.count(AIUsageEvent.id).label("request_count"),
            func.coalesce(func.sum(AIUsageEvent.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(AIUsageEvent.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(AIUsageEvent.total_tokens), 0).label("total_tokens"),
        )
        query = self._apply_filters(
            query,
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id,
            channel_id=channel_id,
        )
        query = query.group_by(period).order_by(period.asc())

        rows = self.db.execute(query).all()
        return [
            {
                "period_start": row.period_start,
                "request_count": int(row.request_count or 0),
                "input_tokens": int(row.input_tokens or 0),
                "output_tokens": int(row.output_tokens or 0),
                "total_tokens": int(row.total_tokens or 0),
            }
            for row in rows
        ]

    def get_event_by_request_id(self, request_id: str) -> AIUsageEvent | None:
        query = (
            select(AIUsageEvent)
            .where(AIUsageEvent.request_id == request_id)
            .order_by(AIUsageEvent.created_at.desc())
            .limit(1)
        )
        return self.db.execute(query).scalar_one_or_none()

    def _apply_filters(
        self,
        query,
        *,
        start_date: datetime | None,
        end_date: datetime | None,
        tenant_id: uuid.UUID | None,
        channel_id: uuid.UUID | None,
    ):
        if start_date is not None:
            query = query.where(AIUsageEvent.created_at >= start_date)
        if end_date is not None:
            query = query.where(AIUsageEvent.created_at <= end_date)
        if tenant_id is not None:
            query = query.where(AIUsageEvent.tenant_id == tenant_id)
        if channel_id is not None:
            query = query.where(AIUsageEvent.channel_id == channel_id)
        return query
