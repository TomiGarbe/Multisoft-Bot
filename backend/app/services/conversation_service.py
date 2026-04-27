import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.auth import TenantUser
from app.models.conversation import Conversation


def get_conversations(db: Session, user_id: Optional[uuid.UUID] = None) -> list:
    # DEV: bypass user filtering
    if user_id is None:
        conversations = (
            db.query(Conversation)
            .order_by(Conversation.last_message_at.desc())
            .all()
        )
        return [
            {
                "id": str(c.id),
                "tenant_id": str(c.tenant_id),
                "status": c.status,
                "started_at": c.started_at.isoformat() if c.started_at else None,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            }
            for c in conversations
        ]

    tenant_users = (
        db.query(TenantUser)
        .filter(TenantUser.user_id == user_id, TenantUser.is_active == True)
        .all()
    )
    tenant_ids = [tu.tenant_id for tu in tenant_users if tu.tenant_id]
    if not tenant_ids:
        return []

    conversations = (
        db.query(Conversation)
        .filter(Conversation.tenant_id.in_(tenant_ids))
        .order_by(Conversation.last_message_at.desc())
        .all()
    )
    return [
        {
            "id": str(c.id),
            "tenant_id": str(c.tenant_id),
            "status": c.status,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
        }
        for c in conversations
    ]
