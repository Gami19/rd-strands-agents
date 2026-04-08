from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.config.env import load_app_env
from src.infrastructure.seed_projects import ensure_seed_team_projects
from .upload_api import router as upload_router
from .agents_api import router as agents_router
from .skills_api import router as skills_router
from .projects_api import router as projects_router
from src.domain.chat.service import (
    AgentsMultiChatRequest,
    ChatRequest,
    ChatResumeRequest,
    stream_agents_multi_chat,
    stream_chat,
    stream_chat_resume,
)


load_app_env()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_seed_team_projects()
    yield


app = FastAPI(title="Strands Chat API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(skills_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    return await stream_chat(body, request)


@app.post("/api/chat/agents-multi")
async def chat_agents_multi(
    body: AgentsMultiChatRequest, request: Request
) -> StreamingResponse:
    return await stream_agents_multi_chat(body, request)


@app.post("/api/chat/resume")
async def chat_stream_resume(
    body: ChatResumeRequest, request: Request
) -> StreamingResponse:
    return await stream_chat_resume(body, request)

