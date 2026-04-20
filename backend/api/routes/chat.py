"""Chat endpoints — standard and streaming."""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.rag_agent import answer, answer_stream

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    release_filter: str | None = None
    series_filter: str | None = None


class Source(BaseModel):
    spec_name: str
    spec_number: str
    release: str
    series: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    sub_queries: list[str]


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    filters = {}
    if req.release_filter:
        filters["release"] = req.release_filter
    if req.series_filter:
        filters["series"] = req.series_filter

    result = answer(req.question, filters=filters or None)
    return ChatResponse(**result)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Server-sent events stream for real-time token output."""
    filters = {}
    if req.release_filter:
        filters["release"] = req.release_filter
    if req.series_filter:
        filters["series"] = req.series_filter

    async def event_generator():
        async for event in answer_stream(req.question, filters=filters or None):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
