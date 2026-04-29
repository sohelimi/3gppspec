#!/bin/bash
set -e

# Cloud Run requires port 8080 to respond quickly or it kills the container.
# Strategy: start nginx immediately (port 8080 opens), then start services.
# nginx returns 502 for a few seconds while upstreams warm up — that's fine.

# ── Start nginx immediately so Cloud Run sees port 8080 ───────────────────────
nginx -g "daemon off;" -c /etc/nginx/nginx.conf &

# ── Start Next.js frontend ────────────────────────────────────────────────────
PORT=3000 HOSTNAME=127.0.0.1 node /app/frontend_standalone/server.js &

# ── Start FastAPI — ChromaDB is bundled in the image at /app/data/chromadb ───
# Loads from local disk in ~5s; no GCS mount needed.
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &

# Keep container alive
wait
