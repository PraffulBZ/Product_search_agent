import json
from typing import List
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from ..schemas import ChatRequest, ChatResponse, Message
from ..redis_client import get_redis
from ..config import OPENAI_API_KEY, OPENAI_MODEL

router = APIRouter(prefix="", tags=["chat"])

def _redis_key(session_id: str) -> str:
    return f"chat:{session_id}:messages"

def _load_messages(session_id: str) -> List[Message]:
    r = get_redis()
    raw = r.get(_redis_key(session_id))
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [Message(**m) for m in data]
    except Exception:
        return []

def _save_messages(session_id: str, messages: List[Message]) -> None:
    r = get_redis()
    r.set(_redis_key(session_id), json.dumps([m.model_dump() for m in messages]))

@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    history: List[Message] = body.messages if body.messages is not None else _load_messages(body.session_id)
    history.append(Message(role="user", content=body.message))

    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[{"role": m.role, "content": m.content} for m in history],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {e}")

    reply_text = getattr(response, "output_text", None)
    if not reply_text:
        try:
            reply_text = response.output[0].content[0].text if getattr(response, "output", None) else ""
        except Exception:
            reply_text = ""

    if not reply_text:
        raise HTTPException(status_code=502, detail="Failed to extract reply from OpenAI response")

    history.append(Message(role="assistant", content=reply_text))

    try:
        _save_messages(body.session_id, history)
    except Exception as e:
        history.append(Message(role="system", content=f"[warning] failed to save state: {e}"))

    return ChatResponse(
        reply=reply_text,
        session_id=body.session_id,
        messages=history,
    )
