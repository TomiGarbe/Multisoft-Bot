from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.bot_action import BotActionExecution


class BotActionExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, execution: BotActionExecution) -> BotActionExecution:
        self.db.add(execution)
        return execution

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

