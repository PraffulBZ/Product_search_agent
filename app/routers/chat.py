import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from ..schemas import ChatRequest, ChatResponse, Message, State
from ..redis_client import get_redis
from ..config import OPENAI_API_KEY, OPENAI_MODEL

router = APIRouter(prefix="", tags=["chat"])

def _messages_key(session_id: str) -> str:
    return f"chat:{session_id}:messages"

def _state_key(session_id: str) -> str:
    return f"chat:{session_id}:state"

def _summary_key(session_id: str) -> str:
    return f"chat:{session_id}:summary"

def _load_messages(session_id: str) -> List[Message]:
    r = get_redis()
    raw = r.get(_messages_key(session_id))
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [Message(**m) for m in data]
    except Exception:
        return []

def _save_messages(session_id: str, messages: List[Message]) -> None:
    r = get_redis()
    r.set(_messages_key(session_id), json.dumps([m.model_dump() for m in messages]))

def _load_state(session_id: str) -> State:
    r = get_redis()
    raw = r.get(_state_key(session_id))
    if not raw:
        return State()
    try:
        data = json.loads(raw)
        return State(**data)
    except Exception:
        return State()

def _save_state(session_id: str, state: State) -> None:
    r = get_redis()
    r.set(_state_key(session_id), json.dumps(state.model_dump()))

def _load_summary(session_id: str) -> str:
    r = get_redis()
    val = r.get(_summary_key(session_id))
    return val or ""

def _save_summary(session_id: str, summary: str) -> None:
    r = get_redis()
    truncated = summary[:1500] if summary else ""
    r.set(_summary_key(session_id), truncated)

@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    history: List[Message] = body.messages if body.messages is not None else _load_messages(body.session_id)
    history.append(Message(role="user", content=body.message))

    state = _load_state(body.session_id)
    if body.state is not None:
        state = State(
            lang=body.state.lang if body.state.lang is not None else state.lang,
            stage=body.state.stage if body.state.stage is not None else state.stage,
            last_items=body.state.last_items if body.state.last_items is not None else state.last_items,
            selected_sku=body.state.selected_sku if body.state.selected_sku is not None else state.selected_sku,
        )
    summary = _load_summary(body.session_id)
    if body.summary is not None:
        summary = body.summary[:1500]

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
        history.append(Message(role="system", content=f"[warning] failed to save messages: {e}"))

    try:
        _save_state(body.session_id, state)
    except Exception as e:
        history.append(Message(role="system", content=f"[warning] failed to save state: {e}"))

    try:
        _save_summary(body.session_id, summary)
    except Exception as e:
        history.append(Message(role="system", content=f"[warning] failed to save summary: {e}"))

    return ChatResponse(
        reply=reply_text,
        session_id=body.session_id,
        messages=history,
        state=state,
        summary=summary,
    )
