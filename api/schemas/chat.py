from pydantic import BaseModel, EmailStr
from typing import Optional

class ChatMessage(BaseModel):
    input: str