# Stage 1: Build React 18 + Vite frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python 3.12 runtime
FROM python:3.12-slim AS runner
WORKDIR /app

# Install runtime utilities and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary for fast Python package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy backend application source code, configuration, and migrations
COPY backend/ /app/backend/

# Install Python backend dependencies into virtual environment
RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv --no-cache -e "/app/backend"

# Copy compiled frontend distribution from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy entrypoint script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Set environment paths and runtime defaults
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/backend" \
    PORT=8000 \
    APP_ENV=production

EXPOSE 8000

ENTRYPOINT ["/app/start.sh"]
