import uuid
from sqlalchemy.orm import Session

import app.services.message_service as message_service


def send_message(db: Session, data: dict, tenant_id: uuid.UUID) -> dict:
    return message_service.send_message_with_tenant(db, data, tenant_id=tenant_id)
