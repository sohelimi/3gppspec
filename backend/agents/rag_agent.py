"""
Agentic RAG pipeline.
1. Plan: decompose question into sub-queries
2. Retrieve: fetch relevant chunks for each sub-query
3. Generate: synthesize answer with citations
"""

from loguru import logger
from .query_planner import plan_queries
from backend.rag.retriever import retrieve_multi
from backend.llm.groq_client import generate, generate_stream

ANSWER_SYSTEM = """You are a 3GPP telecommunications standards expert assistant.
Answer questions accurately and concisely based ONLY on the provided context from 3GPP specifications.

Rules:
- Cite the spec number (e.g. TS 38.101, TS 23.501) and release when you reference something
- If the context doesn't contain enough information, say so clearly
- Use technical terminology correctly
- Structure long answers with sections when helpful
- Never fabricate spec references or clause numbers
"""


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadata"]
        ref = f"[{i}] {meta.get('spec_name','unknown')} ({meta.get('release','?')}, {meta.get('series','?')})"
        parts.append(f"{ref}\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def _build_sources(chunks: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for chunk in chunks:
        meta = chunk["metadata"]
        key = meta.get("spec_name", "") + meta.get("docx_file", "")
        if key not in seen:
            seen.add(key)
            sources.append({
                "spec_name": meta.get("spec_name", "unknown"),
                "spec_number": meta.get("spec_number", ""),
                "release": meta.get("release", ""),
                "series": meta.get("series", ""),
                "score": chunk.get("score", 0),
            })
    return sources[:6]


def answer(question: str, filters: dict = None) -> dict:
    """
    Full agentic RAG pipeline. Returns answer + sources.
    """
    # Step 1: Plan
    sub_queries = plan_queries(question)
    logger.info(f"Sub-queries: {sub_queries}")

    # Step 2: Retrieve
    chunks = retrieve_multi(sub_queries, n_results=6, filters=filters)
    if not chunks:
        return {
            "answer": "I couldn't find relevant information in the 3GPP specifications. Please try rephrasing your question.",
            "sources": [],
            "sub_queries": sub_queries,
        }

    # Step 3: Generate
    context = _build_context(chunks)
    prompt = f"""Context from 3GPP specifications:

{context}

---

User question: {question}

Answer based on the context above:"""

    response = generate(prompt, system_prompt=ANSWER_SYSTEM, temperature=0.2)

    return {
        "answer": response,
        "sources": _build_sources(chunks),
        "sub_queries": sub_queries,
    }


async def answer_stream(question: str, filters: dict = None):
    """
    Streaming version. Yields answer tokens then a final sources object.
    """
    sub_queries = plan_queries(question)
    chunks = retrieve_multi(sub_queries, n_results=6, filters=filters)

    if not chunks:
        yield {"type": "token", "content": "I couldn't find relevant information in the 3GPP specifications."}
        yield {"type": "done", "sources": [], "sub_queries": sub_queries}
        return

    context = _build_context(chunks)
    prompt = f"""Context from 3GPP specifications:

{context}

---

User question: {question}

Answer based on the context above:"""

    async for token in generate_stream(prompt, system_prompt=ANSWER_SYSTEM, temperature=0.2):
        yield {"type": "token", "content": token}

    yield {"type": "done", "sources": _build_sources(chunks), "sub_queries": sub_queries}
