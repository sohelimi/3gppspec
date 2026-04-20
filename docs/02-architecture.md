# Architecture

## High-Level Design

3gppSpec is built around three core ideas:

1. **Agentic layer** — the system doesn't just do a single vector search; it plans, decomposes, retrieves, and synthesises
2. **Local-first** — embeddings and the vector database run entirely on your machine (zero API cost, no data leaves your infrastructure)
3. **Streaming-first** — answers stream back token-by-token for a responsive user experience

---

## Component Map

```
┌─────────────────────────────────────────────────────────┐
│                    GCP Cloud Run                         │
│                                                         │
│  ┌──────────────┐     ┌──────────────────────────────┐  │
│  │  Next.js UI  │────▶│       FastAPI Backend         │  │
│  │  (port 3000) │◀────│       (port 8080)             │  │
│  └──────────────┘ SSE └──────────────┬───────────────┘  │
│                                      │                   │
│                          ┌───────────▼──────────┐        │
│                          │    Agentic Layer      │        │
│                          │                       │        │
│                          │  ┌─────────────────┐  │        │
│                          │  │  Query Planner  │  │        │
│                          │  │  (Groq LLM)     │  │        │
│                          │  └────────┬────────┘  │        │
│                          │           │            │        │
│                          │  ┌────────▼────────┐  │        │
│                          │  │   RAG Agent     │  │        │
│                          │  └────────┬────────┘  │        │
│                          └───────────┼───────────┘        │
│                                      │                   │
│              ┌───────────────────────┼──────────┐        │
│              │                       │          │        │
│   ┌──────────▼──────┐   ┌────────────▼───────┐  │        │
│   │   ChromaDB      │   │  all-MiniLM-L6-v2  │  │        │
│   │  (vector store) │   │  (embeddings)       │  │        │
│   └─────────────────┘   └────────────────────┘  │        │
└─────────────────────────────────────────────────────────┘
                                      │
                          ┌───────────▼──────────┐
                          │    Groq API           │
                          │  (Llama 3.3 70B)      │
                          │   External call       │
                          └──────────────────────┘
```

---

## Request Lifecycle

When a user submits a question, here is the exact sequence of operations:

### Step 1 — HTTP Request
The Next.js frontend sends a `POST /api/chat/stream` request with the question as JSON.

### Step 2 — Query Planning (Agentic)
The **Query Planner** sends the question to Groq (Llama 3.3 70B) with a system prompt asking it to decompose the question into 2–4 focused sub-queries.

**Example:**
- Input: *"What security mechanisms protect the 5G core network?"*
- Output: `["5G core network security architecture", "authentication in 5G NR", "encryption in 5G core", "TS 33.501 security features"]`

This is the **agentic** part — the system plans its own search strategy rather than doing a single naive lookup.

### Step 3 — Multi-Query Retrieval
For each sub-query, the **Retriever** calls ChromaDB with the embedded query vector and fetches the top-5 most similar chunks. Results from all sub-queries are merged and deduplicated.

### Step 4 — Context Assembly
Retrieved chunks are formatted with their metadata (spec name, release, series) and assembled into a context block.

### Step 5 — LLM Generation (Streaming)
The RAG Agent sends the context + original question to Groq as a streaming request. Tokens stream back as they are generated.

### Step 6 — SSE Stream to Client
Each token is wrapped in a Server-Sent Event and pushed to the frontend. When generation completes, a final `done` event carries the source citations.

### Step 7 — UI Rendering
The Next.js frontend renders tokens in real time using React state updates, and displays source cards once the `done` event arrives.

---

## Data Flow Diagram

```
User Question
     │
     ▼
[Query Planner] ──Groq──▶ ["sub-query 1", "sub-query 2", "sub-query 3"]
     │
     ▼
[Retriever] ──embed──▶ all-MiniLM-L6-v2 ──▶ 384-dim vectors
     │
     ▼
[ChromaDB] ──cosine similarity──▶ Top-8 chunks + metadata
     │
     ▼
[RAG Agent] ──assemble context──▶ Groq (Llama 3.3 70B)
     │
     ▼
[SSE Stream] ──tokens──▶ Next.js UI ──▶ User
```

---

## Technology Choices

### Why Groq + Llama 3.3 70B?
- **Free tier**: 14,400 requests/day — more than enough for a portfolio chatbot
- **No credit card** required
- **Fast inference**: Groq's custom LPU hardware is 10–20x faster than typical cloud GPU inference
- **Open weights**: Llama 3.3 70B is a Meta open-source model — good for a portfolio project's open-source story

### Why all-MiniLM-L6-v2?
- **22MB** model — downloads in seconds, runs on CPU
- **384-dimensional** embeddings — compact and fast
- **Sentence-transformers library** — battle-tested, widely used
- **~15x faster** than larger models like BAAI/bge-large on CPU
- Achieves excellent performance on semantic similarity benchmarks for RAG use cases

### Why ChromaDB?
- **Zero infrastructure** — runs as a Python library, persists to a local folder
- **Cosine similarity** search built in
- **Upsert support** — safe to re-run ingestion without duplicates
- The `./data/chromadb/` folder is bundled into the Docker image for deployment

### Why FastAPI?
- Native **async** support for streaming responses
- **Server-Sent Events** (SSE) work cleanly with `StreamingResponse`
- Auto-generates OpenAPI docs at `/docs`
- Fast startup — important for Cloud Run cold starts

### Why Next.js?
- `output: "standalone"` mode produces a minimal Docker image
- Server components keep the bundle small
- Tailwind CSS for rapid UI development
