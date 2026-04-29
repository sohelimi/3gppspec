"""ChromaDB vector store with local sentence-transformers embeddings."""

import threading
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from loguru import logger

COLLECTION_NAME = "3gpp_specs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Module-level state so health endpoint can check without blocking
_chunks_count: int = 0
_is_ready: bool = False


class VectorStore:
    def __init__(self, persist_path: str):
        self.persist_path = persist_path
        self._client = None
        self._ef = None
        self._lock = threading.Lock()

    def _init(self):
        global _is_ready, _chunks_count
        # Lock prevents a race where one thread sets _client but not yet _ef,
        # causing a second thread to call get_or_create_collection(ef=None)
        # which returns a collection with no embedding function → ValueError.
        with self._lock:
            if self._client is not None:
                return  # Already initialised by another thread

            logger.info(f"Loading ChromaDB from {self.persist_path}")
            # Build embedding function FIRST so _ef is never None when _client is set
            ef = SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL,
                device="cpu",
            )
            logger.info(f"Embedding model loaded: {EMBEDDING_MODEL}")
            client = chromadb.PersistentClient(path=self.persist_path)
            # Assign both together so no thread ever sees client-set / ef-unset
            self._ef = ef
            self._client = client

            # Mark ready and cache chunk count
            try:
                col = self._client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=self._ef,
                    metadata={"hnsw:space": "cosine"},
                )
                _chunks_count = col.count()
                _is_ready = True
                logger.info(f"ChromaDB ready — {_chunks_count} chunks indexed")
            except Exception as e:
                logger.warning(f"ChromaDB count failed: {e}")

    def get_or_create_collection(self):
        self._init()
        return self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    def query(self, query_text: str, n_results: int = 8, where: dict = None) -> list[dict]:
        collection = self.get_or_create_collection()
        kwargs = {"query_texts": [query_text], "n_results": n_results, "include": ["documents", "metadatas", "distances"]}
        if where:
            kwargs["where"] = where
        results = collection.query(**kwargs)

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            {"text": doc, "metadata": meta, "score": round(1 - dist, 4)}
            for doc, meta, dist in zip(docs, metas, distances)
        ]

    def count(self) -> int:
        collection = self.get_or_create_collection()
        return collection.count()


_store: VectorStore | None = None


def get_vectorstore(path: str = None) -> VectorStore:
    global _store
    if _store is None:
        from backend.config import settings
        _store = VectorStore(path or settings.chroma_db_path)
    return _store


def get_vectorstore_status() -> dict:
    """Non-blocking status check — returns instantly regardless of ChromaDB state."""
    if _is_ready:
        return {"status": "ok", "chunks_indexed": _chunks_count}
    return {"status": "loading", "chunks_indexed": 0, "message": "ChromaDB is warming up, please wait ~60s"}
