from typing import List, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    messages: Optional[List[Message]] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    messages: List[Message]
