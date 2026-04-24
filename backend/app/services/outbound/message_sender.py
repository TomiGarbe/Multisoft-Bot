from sqlalchemy.orm import Session

import app.services.message_service as message_service


def send_message(db: Session, data: dict) -> dict:
    return message_service.send_message(db, data)
