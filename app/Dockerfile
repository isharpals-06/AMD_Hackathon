# ─── Backend — Multi-stage, hardened production image ─────────────────────────
# Stage 1: Builder — installs all Python dependencies
FROM python:3.11-slim AS builder

# Prevent .pyc files and buffered output during build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# System deps for chromadb (hnswlib builds from source on slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a clean prefix
COPY requirements.txt ./
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ─── Stage 2: Runtime — minimal image ─────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    # Prometheus multiproc requires a shared dir for worker metrics
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Create non-root user for security hardening
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home appuser && \
    mkdir -p /app/data /tmp/prometheus_multiproc && \
    chown -R appuser:appgroup /app /tmp/prometheus_multiproc

# Copy application source
COPY app/ ./app/

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check — uses lightweight urllib (no extra deps)
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the app with uvicorn (workers=1 for SQLite-safe single process)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]
