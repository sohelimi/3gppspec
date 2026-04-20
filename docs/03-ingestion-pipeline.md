# Ingestion Pipeline

The ingestion pipeline is a one-time process that transforms raw 3GPP ZIP files into a searchable vector database.

## Overview

```
3GPP ZIP files  →  Extract DOCX  →  Parse text  →  Chunk  →  Embed  →  ChromaDB
```

## Running Ingestion

```bash
# Activate virtual environment
source .venv/bin/activate

# Full ingestion (Rel-17, 18, 19 — series 23, 24, 33, 38)
python scripts/ingest.py

# Target specific releases/series
python scripts/ingest.py --releases Rel-18 --series 38_series
python scripts/ingest.py --releases Rel-17,Rel-18 --series 23_series,38_series

# Custom paths
python scripts/ingest.py \
  --specs-dir /path/to/3gpp_specs \
  --chroma-path ./data/chromadb
```

**Expected time:** ~30 minutes per major series on a modern CPU.

---

## Pipeline Stages

### Stage 1 — ZIP Discovery (`extractor.py`)

Walks the specs directory tree to find all matching ZIP files:

```
/3gpp_specs_2024_09/
  Rel-18/
    38_series/
      38101-1-i70.zip   ← discovered
      38101-2-i70.zip   ← discovered
      ...
```

Each ZIP contains multiple `.docx` files split by section (e.g. `38101-1-i70_s06-06.docx`).

### Stage 2 — DOCX Extraction (`extractor.py`)

For each ZIP:
1. Opens the ZIP in memory (no temp files)
2. Finds all `.docx` entries
3. Parses each DOCX using `python-docx`:
   - Extracts all paragraph text
   - Extracts table cell content
   - Skips near-empty documents (< 200 chars)
4. Attaches metadata: `release`, `series`, `spec_number`, `spec_name`, `zip_file`, `docx_file`

### Stage 3 — Text Chunking (`chunker.py`)

Splits extracted text into overlapping chunks:

| Parameter | Value | Reason |
|---|---|---|
| Chunk size | 800 characters | Fits within embedding model context, captures enough context |
| Overlap | 150 characters | Prevents losing context at chunk boundaries |
| Split strategy | Paragraph-first | Respects natural document boundaries |

**Example:**
```
[Paragraph 1] [Paragraph 2] [Paragraph 3] [Paragraph 4]
     ↓
Chunk 1: [Para 1] [Para 2]            (800 chars)
Chunk 2:          [Para 2*] [Para 3]  (800 chars, 150 char overlap)
Chunk 3:                    [Para 3*] [Para 4]
```

### Stage 4 — Embedding (`vectorstore.py`)

Each chunk's text is converted to a 384-dimensional vector using `all-MiniLM-L6-v2`:

```python
embedding = model.encode("What is the subcarrier spacing in 5G NR numerology 2?")
# → [0.023, -0.145, 0.891, ...] (384 floats)
```

The model runs entirely on CPU — no GPU needed, no API calls.

### Stage 5 — Storage (`vectorstore.py` + ChromaDB)

Chunks are upserted into ChromaDB in batches of 100:

```python
collection.upsert(
    ids=["md5_hash_1", "md5_hash_2", ...],
    documents=["chunk text...", ...],
    metadatas=[{"release": "Rel-18", "series": "38_series", ...}, ...],
)
```

**ID generation:** MD5 hash of `zip_name::docx_name::chunk_index` — ensures upsert is idempotent (safe to re-run).

---

## ChromaDB Structure

```
./data/chromadb/
  chroma.sqlite3          ← metadata, IDs, collection config
  <uuid>/
    data_level0.bin       ← HNSW index (vector similarity graph)
    header.bin
    length.bin
    link_lists.bin
```

**Collection config:**
- Name: `3gpp_specs`
- Distance metric: cosine similarity
- Embedding dimension: 384

---

## Chunk Metadata Schema

Every chunk stored in ChromaDB carries this metadata:

| Field | Example | Description |
|---|---|---|
| `release` | `Rel-18` | 3GPP release |
| `series` | `38_series` | Spec series |
| `spec_number` | `38101` | TS number |
| `spec_name` | `38101-1-i70` | Full spec filename |
| `zip_file` | `38101-1-i70.zip` | Source ZIP |
| `docx_file` | `38101-1-i70_s06-06.docx` | Source DOCX section |

---

## Scale

| Series | Size | Est. Chunks | Est. Time |
|---|---|---|---|
| 38_series (Rel-18) | 496MB | ~230,000 | ~35 min |
| 23_series (Rel-18) | 368MB | ~150,000 | ~25 min |
| 33_series (Rel-18) | 71MB | ~30,000 | ~5 min |
| 24_series (Rel-18) | 79MB | ~35,000 | ~5 min |
| **Total (Rel-18 key series)** | **~1GB** | **~445,000** | **~70 min** |

---

## Re-running Ingestion

The pipeline is fully **idempotent** — re-running it on already-processed specs will upsert the same IDs and produce no duplicates. This means you can safely:

- Add new releases without clearing the DB
- Re-run after a crash to pick up where you left off
- Add new series incrementally
