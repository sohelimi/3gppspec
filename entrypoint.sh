#!/bin/bash
set -e

# Copy ChromaDB from GCS-mounted volume to local fast storage
# GCS FUSE is too slow for ChromaDB's random HNSW index reads
if [ -d "/data/chromadb" ] && [ ! -d "/tmp/chromadb/chroma.sqlite3" ]; then
  echo "Copying ChromaDB from GCS mount to local disk..."
  cp -r /data/chromadb /tmp/chromadb
  echo "ChromaDB copy complete."
fi

export CHROMA_DB_PATH=/tmp/chromadb

exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8080}"
