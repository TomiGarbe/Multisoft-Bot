from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.ai.ai_logs import AILog


class AILogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, data: dict) -> AILog:
        log = AILog(**data)
        self.db.add(log)
        self.db.flush()
        return log

    def get_by_request_id(self, request_id: str) -> list[AILog]:
        query = select(AILog).where(AILog.request_id == request_id).order_by(AILog.created_at.asc())
        return list(self.db.execute(query).scalars().all())
