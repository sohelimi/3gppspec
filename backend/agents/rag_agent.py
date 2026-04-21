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

Answer using the following priority:
1. If the provided 3GPP spec context is relevant, base your answer on it and cite the spec (e.g. TS 38.101, TS 23.501) and release.
2. If the context is insufficient or irrelevant, answer from your expert knowledge of 3GPP/5G/LTE telecommunications — clearly stating "Based on general 3GPP knowledge:" so the user knows it is not directly from the indexed specs.

Rules:
- Never fabricate spec references or clause numbers
- Use technical terminology correctly
- Structure long answers with sections when helpful
- Always be clear whether your answer comes from the indexed specs or general knowledge
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

    # Step 3: Generate (always — falls back to LLM general knowledge if no chunks)
    context = _build_context(chunks) if chunks else "No relevant chunks found in the indexed 3GPP specifications."
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

    context = _build_context(chunks) if chunks else "No relevant chunks found in the indexed 3GPP specifications."
    prompt = f"""Context from 3GPP specifications:

{context}

---

User question: {question}

Answer based on the context above:"""

    async for token in generate_stream(prompt, system_prompt=ANSWER_SYSTEM, temperature=0.2):
        yield {"type": "token", "content": token}

    yield {"type": "done", "sources": _build_sources(chunks), "sub_queries": sub_queries}
