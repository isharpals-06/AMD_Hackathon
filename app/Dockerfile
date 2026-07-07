# ─── Backend ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered stdout/stderr for clean Docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps required by chromadb (hnswlib builds from source on slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer-cached until requirements.txt changes)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

# Create the data directory so SQLite + ChromaDB paths resolve immediately
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 8000

# Health check so docker-compose can wait for the backend to be ready
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
