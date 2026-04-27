#!/bin/bash
set -e

# ── Step 1: Copy ChromaDB from GCS mount to container disk ────────────────────
# /tmp in Cloud Run gen2 is memory-backed (tmpfs, ~1GB limit).
# Use /chromadb-local which is disk-backed and has plenty of space.
if [ -d "/data/chromadb" ]; then
  echo "[startup] Copying ChromaDB from GCS to local disk..."
  mkdir -p /chromadb-local
  cp -r /data/chromadb /chromadb-local/chromadb
  echo "[startup] ChromaDB ready ($(du -sh /chromadb-local/chromadb | cut -f1))"
fi

export CHROMA_DB_PATH=/chromadb-local/chromadb

# ── Step 2: Start FastAPI and Next.js ─────────────────────────────────────────
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
PORT=3000 HOSTNAME=127.0.0.1 node /app/frontend_standalone/server.js &

# ── Step 3: Wait for both services to be ready before starting nginx ──────────
echo "[startup] Waiting for backend and frontend..."
until curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; do sleep 1; done
echo "[startup] Backend ready"
until curl -sf http://127.0.0.1:3000 > /dev/null 2>&1; do sleep 1; done
echo "[startup] Frontend ready"

# ── Step 4: Start nginx (now both upstreams are up) ───────────────────────────
exec nginx -g "daemon off;" -c /etc/nginx/nginx.conf
