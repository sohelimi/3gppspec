from fastapi import APIRouter
from backend.rag.vectorstore import get_vectorstore_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """
    Lightweight health check — never blocks on ChromaDB initialization.
    Returns status + chunk count if already loaded, or 'loading' if still warming up.
    """
    status = get_vectorstore_status()
    return status
