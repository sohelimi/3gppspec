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

# Copy built frontend into FastAPI static files
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend_standalone/
COPY --from=frontend-builder /app/frontend/.next/static ./frontend_standalone/.next/static/
COPY --from=frontend-builder /app/frontend/public ./frontend_standalone/public/

# Copy ChromaDB (pre-built during CI or mounted as volume)
COPY data/ ./data/

# Pre-download embedding model at build time so container starts fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5')"

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
