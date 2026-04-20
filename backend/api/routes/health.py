from fastapi import APIRouter
from backend.rag.vectorstore import get_vectorstore

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    try:
        count = get_vectorstore().count()
        return {"status": "ok", "chunks_indexed": count}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
