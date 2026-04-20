"""Full ingestion pipeline: ZIP files → ChromaDB."""

import hashlib
from pathlib import Path
from tqdm import tqdm
from loguru import logger

from .extractor import iter_spec_zips, extract_zip, parse_spec_metadata
from .chunker import chunk_text
from ..vectorstore import get_vectorstore


def _doc_id(zip_name: str, docx_name: str, chunk_idx: int) -> str:
    raw = f"{zip_name}::{docx_name}::{chunk_idx}"
    return hashlib.md5(raw.encode()).hexdigest()


def run_ingestion(specs_dir: str, releases: list[str], series: list[str], chroma_path: str, batch_size: int = 100):
    """
    Extract, chunk, embed, and store all matching specs into ChromaDB.
    Safe to re-run — skips already-ingested documents.
    """
    store = get_vectorstore(chroma_path)
    collection = store.get_or_create_collection()

    zip_paths = list(iter_spec_zips(specs_dir, releases, series))
    logger.info(f"Found {len(zip_paths)} ZIP files to process")

    total_chunks = 0
    ids_batch, texts_batch, metas_batch = [], [], []

    for zip_path in tqdm(zip_paths, desc="Processing ZIPs"):
        metadata_base = parse_spec_metadata(zip_path)

        for docx_name, text in extract_zip(zip_path):
            meta = {**metadata_base, "docx_file": docx_name}
            for idx, chunk in enumerate(chunk_text(text, meta)):
                doc_id = _doc_id(zip_path.name, docx_name, idx)
                ids_batch.append(doc_id)
                texts_batch.append(chunk["text"])
                metas_batch.append(chunk["metadata"])
                total_chunks += 1

                if len(ids_batch) >= batch_size:
                    _upsert_batch(collection, ids_batch, texts_batch, metas_batch)
                    ids_batch, texts_batch, metas_batch = [], [], []

    if ids_batch:
        _upsert_batch(collection, ids_batch, texts_batch, metas_batch)

    logger.success(f"Ingestion complete. Total chunks stored: {total_chunks}")
    return total_chunks


def _upsert_batch(collection, ids, texts, metas):
    try:
        collection.upsert(ids=ids, documents=texts, metadatas=metas)
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}")
