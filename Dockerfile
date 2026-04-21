# ── Stage 1: Build Next.js frontend ──────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# ── Stage 2: Runtime (Python + Node + nginx) ──────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# System deps: nginx, Node.js, libgomp (sentence-transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    libgomp1 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy built Next.js standalone
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend_standalone/
COPY --from=frontend-builder /app/frontend/.next/static ./frontend_standalone/.next/static/
COPY --from=frontend-builder /app/frontend/public ./frontend_standalone/public/

# nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Pre-download embedding model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

ENV CHROMA_DB_PATH=/data/chromadb
ENV PORT=8080
ENV HOSTNAME=0.0.0.0
EXPOSE 8080

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
