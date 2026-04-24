#!/bin/bash
set -e

# ── Step 1: Copy ChromaDB from GCS mount to local NVMe ────────────────────────
# GCS FUSE is slow for random reads (HNSW index). Copying to /tmp first means
# the first request is served from fast local disk, not over the network.
if [ -d "/data/chromadb" ]; then
  echo "[startup] Copying ChromaDB from GCS to local disk..."
  cp -r /data/chromadb /tmp/chromadb
  echo "[startup] ChromaDB ready ($(du -sh /tmp/chromadb | cut -f1))"
fi

export CHROMA_DB_PATH=/tmp/chromadb

# ── Step 2: Start services ─────────────────────────────────────────────────────
# FastAPI backend on port 8000
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &

# Next.js frontend on port 3000
PORT=3000 HOSTNAME=127.0.0.1 node /app/frontend_standalone/server.js &

# nginx reverse proxy on port 8080 (Cloud Run public port)
exec nginx -g "daemon off;" -c /etc/nginx/nginx.conf
