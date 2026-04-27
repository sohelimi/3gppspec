"""ChromaDB vector store with local sentence-transformers embeddings."""

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

    def _init(self):
        global _is_ready, _chunks_count
        if self._client is None:
            logger.info(f"Loading ChromaDB from {self.persist_path}")
            self._client = chromadb.PersistentClient(path=self.persist_path)
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            self._ef = SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL,
                device="cpu",
            )
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
