from __future__ import annotations

from typing import Any, Optional, TypeVar

from sqlalchemy.orm import Session

TModel = TypeVar("TModel")


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, model: type[TModel], entity_id: Any) -> Optional[TModel]:
        return self.db.get(model, entity_id)

    def delete(self, entity: Any) -> None:
        self.db.delete(entity)

    def commit(self) -> None:
        self.db.commit()
