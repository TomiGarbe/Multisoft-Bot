from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.metrics import TokenUsage
from app.repositories.base_repository import BaseRepository


class TokenUsageRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create_usage(
        self,
        *,
        tenant_id: uuid.UUID,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        model: Optional[str] = None,
    ) -> TokenUsage:
        usage = TokenUsage(
            tenant_id=tenant_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
        )
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage

    def get_total_tokens_by_tenant(self, tenant_id: uuid.UUID) -> int:
        query = select(func.coalesce(func.sum(TokenUsage.total_tokens), 0)).where(
            TokenUsage.tenant_id == tenant_id
        )
        return int(self.db.execute(query).scalar_one())

    def get_total_tokens_by_tenant_and_range(
        self,
        *,
        tenant_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        query = select(func.coalesce(func.sum(TokenUsage.total_tokens), 0)).where(
            TokenUsage.tenant_id == tenant_id,
            TokenUsage.created_at >= start_date,
            TokenUsage.created_at <= end_date,
        )
        return int(self.db.execute(query).scalar_one())
