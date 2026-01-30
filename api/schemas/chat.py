from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ChatMessage(BaseModel):
    input: str


class ChatHistory(BaseModel):
    id: int
    user_id: int
    content: str
    type: str
    reply_id: Optional[int] = None
    timestamp: datetime