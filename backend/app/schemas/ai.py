import uuid
from typing import Optional

from pydantic import BaseModel


class AITestRequest(BaseModel):
    message: str
    channel_id: uuid.UUID
    contact_id: Optional[uuid.UUID] = None


class AITestResponse(BaseModel):
    response: str
    prompt: str

