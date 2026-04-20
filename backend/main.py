"""3gppSpec — 3GPP RAG Chatbot API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.routes.chat import router as chat_router
from backend.api.routes.health import router as health_router

app = FastAPI(
    title="3gppSpec — 3GPP AI Assistant",
    description="Agentic RAG chatbot over 3GPP specifications",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"name": "3gppSpec 3GPP AI Assistant", "status": "running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
