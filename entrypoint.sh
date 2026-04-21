#!/bin/bash
set -e

# Start FastAPI backend on port 8000
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &

# Start Next.js frontend on port 3000 (explicit, ignores PORT env var)
PORT=3000 HOSTNAME=127.0.0.1 node /app/frontend_standalone/server.js &

# Start nginx on port 8080 (Cloud Run's public port)
exec nginx -g "daemon off;" -c /etc/nginx/nginx.conf
