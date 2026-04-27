from sqlalchemy.orm import Session

from app.models.ai.ai_logs import AILog


class AILogRepository:

    async def create_log(self, db: Session, data: dict) -> AILog:
        log = AILog(**data)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
