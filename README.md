# Product Search Agent – FastAPI + Redis + OpenAI Responses

This service exposes a POST `/chat` endpoint that maintains per-session conversation state in Redis and generates replies using the OpenAI Responses API.

## Requirements
- Python 3.12
- Redis server (default URL: `redis://localhost:6379/0`)
- OpenAI API key

## Setup
1. Install dependencies:
   pip install -r requirements.txt

2. Configure environment (create `.env` in repo root):
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini
   REDIS_URL=redis://localhost:6379/0

3. Run the server:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Example
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "test-123",
        "message": "Hello!"
      }'

Response:
{
  "reply": "...",
  "session_id": "test-123",
  "messages": [
    {"role":"user","content":"Hello!"},
    {"role":"assistant","content":"..."}
  ]
}

## Notes
- If Redis is down, the API will still return a reply but may add a system warning in messages.
- To reset state, delete the key `chat:{session_id}:messages` in Redis.
