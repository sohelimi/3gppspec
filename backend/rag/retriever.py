"""Retriever: fetch and rerank relevant chunks from ChromaDB."""

from .vectorstore import get_vectorstore


def retrieve(query: str, n_results: int = 8, filters: dict = None) -> list[dict]:
    """
    Retrieve top-n chunks for a query with optional metadata filters.

    filters example: {"release": "Rel-18"} or {"series": "38_series"}
    """
    store = get_vectorstore()
    return store.query(query, n_results=n_results, where=filters)


def retrieve_multi(queries: list[str], n_results: int = 5, filters: dict = None) -> list[dict]:
    """
    Retrieve chunks for multiple sub-queries and deduplicate by ID.
    Used by the query planning agent for multi-hop questions.
    """
    store = get_vectorstore()
    seen_texts = set()
    all_results = []

    for q in queries:
        results = store.query(q, n_results=n_results, where=filters)
        for r in results:
            key = r["text"][:100]
            if key not in seen_texts:
                seen_texts.add(key)
                all_results.append(r)

    # Sort by score descending
    return sorted(all_results, key=lambda x: x["score"], reverse=True)
