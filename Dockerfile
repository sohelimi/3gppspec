# ── Stage 1: Build Next.js frontend ──────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# ── Stage 2: Python backend + serve frontend ──────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# System deps for python-docx and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend_standalone/
COPY --from=frontend-builder /app/frontend/.next/static ./frontend_standalone/.next/static/
COPY --from=frontend-builder /app/frontend/public ./frontend_standalone/public/

# Pre-download embedding model so container starts fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ChromaDB is mounted from GCS and copied to local disk at startup
ENV CHROMA_DB_PATH=/data/chromadb
ENV PORT=8080
EXPOSE 8080

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
