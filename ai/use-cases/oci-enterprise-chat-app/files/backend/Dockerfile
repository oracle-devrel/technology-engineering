# =============================================================================
# Dockerfile — AIQ RAG Backend (FastAPI + Oracle 23ai Vector Store)
# =============================================================================
# Build context: backend/
# Build:  docker build -t aiq-backend:latest ./backend
# Run:    docker run -p 8000:8000 --env-file ./backend/.env aiq-backend:latest
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Dependency builder
# ---------------------------------------------------------------------------
# Install Python packages in a throwaway stage so that build tools, pip cache,
# and compiler artefacts never land in the final image.
# ---------------------------------------------------------------------------
FROM python:3.12 AS builder

WORKDIR /build

# python:3.12 (full) already includes gcc and libc6-dev, so no apt-get needed.

COPY requirements.txt .

# Install production-only dependencies into a virtual environment.
# We filter out dev/test packages (pytest*, ruff) at install time by
# generating a stripped requirements file.
RUN grep -viE '^\s*(pytest|ruff)' requirements.txt > requirements-prod.txt && \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements-prod.txt

# ---------------------------------------------------------------------------
# Stage 2: Production runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL maintainer="ai-coe" \
      description="AIQ RAG Backend — FastAPI + Oracle 23ai Vector Store" \
      version="1.0.0"

WORKDIR /app

# Copy the pre-built virtual environment from the builder stage.
# The venv was created at /opt/venv in both stages so shebangs are correct.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# --- Security: run as non-root ---
RUN groupadd --gid 1001 appgroup && \
    useradd  --uid 1001 --gid appgroup --shell /bin/false --create-home appuser

# Create directories the app needs at runtime:
#   /app/uploads  — temporary PDF storage
#   /app/config   — Oracle wallet location
RUN mkdir -p /app/uploads /app/config/wallet && \
    chown -R appuser:appgroup /app

# Copy Oracle wallet (mTLS credentials for Autonomous Database)
# Wallet files are read-only; restrict permissions accordingly.
COPY --chown=appuser:appgroup config/wallet/ /app/config/wallet/
RUN chmod 600 /app/config/wallet/*.sso /app/config/wallet/*.p12 /app/config/wallet/*.pem 2>/dev/null; \
    chmod 644 /app/config/wallet/*.ora /app/config/wallet/*.properties 2>/dev/null; \
    true

# Copy application source code (after deps, to maximise layer-cache hits)
COPY --chown=appuser:appgroup main.py        /app/main.py
COPY --chown=appuser:appgroup schemas.py     /app/schemas.py
COPY --chown=appuser:appgroup models/        /app/models/
COPY --chown=appuser:appgroup routers/       /app/routers/
COPY --chown=appuser:appgroup services/      /app/services/

# Switch to non-root user
USER appuser

# Expose the FastAPI default port
EXPOSE 8000

# Healthcheck — matches the /health endpoint defined in main.py
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Entrypoint: production uvicorn server
# --workers defaults to 1; override via $WEB_CONCURRENCY at runtime.
# --no-access-log keeps stdout clean when a reverse-proxy already logs requests.
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--no-access-log"]
