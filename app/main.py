from fastapi import FastAPI
from .config import APP_NAME
from .routers.chat import router as chat_router

def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME)
    app.include_router(chat_router)
    return app

app = create_app()
