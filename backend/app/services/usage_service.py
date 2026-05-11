from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.config import ChannelBotConfig
from app.models.contact import Contact
from app.models.metrics import AIUsageEvent
from app.models.tenant import Tenant
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

    def get_contacts_summary(self, *, tenant_id: uuid.UUID | None = None) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        total_query = select(func.count(Contact.id))
        month_query = select(func.count(Contact.id)).where(Contact.created_at >= month_start)
        by_type_query = (
            select(
                Contact.current_type,
                func.count(Contact.id).label("total_count"),
                func.sum(case((Contact.created_at >= month_start, 1), else_=0)).label("new_count"),
            )
            .group_by(Contact.current_type)
        )

        if tenant_id is not None:
            total_query = total_query.where(Contact.tenant_id == tenant_id)
            month_query = month_query.where(Contact.tenant_id == tenant_id)
            by_type_query = by_type_query.where(Contact.tenant_id == tenant_id)

        total_contacts = int(self.db.execute(total_query).scalar() or 0)
        new_contacts_month = int(self.db.execute(month_query).scalar() or 0)

        rows = self.db.execute(by_type_query).all()
        by_type = []
        for row in rows:
            key = str(row.current_type).strip() if row.current_type else "sin_tipo"
            by_type.append(
                {
                    "key": key,
                    "label": key.replace("_", " ").title(),
                    "total": int(row.total_count or 0),
                    "new_this_month": int(row.new_count or 0),
                }
            )

        by_type.sort(key=lambda item: item["total"], reverse=True)
        return {
            "total_contacts": total_contacts,
            "new_contacts_this_month": new_contacts_month,
            "by_type": by_type,
            "month_start": month_start.isoformat(),
        }

    def get_token_usage_by_channel(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        query = (
            select(
                AIUsageEvent.channel_id,
                Channel.name,
                func.coalesce(func.sum(AIUsageEvent.total_tokens), 0).label("total_tokens"),
            )
            .join(Channel, Channel.id == AIUsageEvent.channel_id)
            .group_by(AIUsageEvent.channel_id, Channel.name)
            .order_by(func.coalesce(func.sum(AIUsageEvent.total_tokens), 0).desc())
        )
        if tenant_id is not None:
            query = query.where(AIUsageEvent.tenant_id == tenant_id)
        if start_date is not None:
            query = query.where(AIUsageEvent.created_at >= start_date)
        if end_date is not None:
            query = query.where(AIUsageEvent.created_at <= end_date)
        rows = self.db.execute(query).all()
        return [
            {
                "channel_id": str(row.channel_id),
                "channel_name": row.name,
                "total_tokens": int(row.total_tokens or 0),
            }
            for row in rows
        ]

    def get_token_usage_by_tenant(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        query = (
            select(
                AIUsageEvent.tenant_id,
                Tenant.name,
                func.coalesce(func.sum(AIUsageEvent.total_tokens), 0).label("total_tokens"),
            )
            .join(Tenant, Tenant.id == AIUsageEvent.tenant_id)
            .group_by(AIUsageEvent.tenant_id, Tenant.name)
            .order_by(func.coalesce(func.sum(AIUsageEvent.total_tokens), 0).desc())
        )
        if start_date is not None:
            query = query.where(AIUsageEvent.created_at >= start_date)
        if end_date is not None:
            query = query.where(AIUsageEvent.created_at <= end_date)
        rows = self.db.execute(query).all()
        return [
            {
                "tenant_id": str(row.tenant_id),
                "tenant_name": row.name,
                "total_tokens": int(row.total_tokens or 0),
            }
            for row in rows
        ]

    def get_configured_conversion_flows(self, *, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
        query = select(ChannelBotConfig.user_types_jsonb, ChannelBotConfig.config_jsonb).where(
            ChannelBotConfig.tenant_id == tenant_id,
            ChannelBotConfig.is_active.is_(True),
        )
        rows = self.db.execute(query).all()
        edges: dict[tuple[str, str], None] = {}
        for row in rows:
            config_jsonb = row.config_jsonb if isinstance(row.config_jsonb, dict) else {}
            objectives = config_jsonb.get("objectives") if isinstance(config_jsonb, dict) else []
            if not isinstance(objectives, list):
                continue
            for objective in objectives:
                if not isinstance(objective, dict):
                    continue
                target = objective.get("on_completion")
                applies_to = objective.get("applies_to")
                if not isinstance(target, str) or not target.strip():
                    continue
                if not isinstance(applies_to, list):
                    continue
                for source in applies_to:
                    if isinstance(source, str) and source.strip() and source.strip() != target.strip():
                        edges[(source.strip(), target.strip())] = None

        return [
            {
                "from_type": source,
                "to_type": target,
            }
            for source, target in edges.keys()
        ]
