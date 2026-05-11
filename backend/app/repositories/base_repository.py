from __future__ import annotations

import logging
from typing import Any, Optional, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

TModel = TypeVar("TModel")
logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, model: type[TModel], entity_id: Any) -> Optional[TModel]:
        return self.db.get(model, entity_id)

    def delete(self, entity: Any) -> None:
        self.db.delete(entity)

    def commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError:
            logger.exception("Database commit failed")
            self.db.rollback()
            raise
