from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class State(BaseModel):
    lang: str = "en"
    stage: str = ""
    last_items: List[str] = []
    selected_sku: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: str
    message: str
    messages: Optional[List[Message]] = None
    state: Optional[State] = None
    summary: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    messages: List[Message]
    state: State
    summary: str
