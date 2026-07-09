# Deployment Guide

## Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Service orchestration |
| Git | 2.40+ | Version control |
| (Optional) AMD ROCm | 6.0+ | GPU acceleration |

---

## Environment Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/AMD-Hackathon.git
cd AMD-Hackathon

# 2. Copy and configure environment
cp .env.example .env
```

**Edit `.env` and set at minimum:**

```env
FIREWORKS_API_KEY=your_fireworks_api_key_here
GRAFANA_ADMIN_PASSWORD=your_secure_password_here
```

---

## Docker Compose Deployment (Recommended)

### Start All Services

```bash
# Build images
docker compose build

# Start all services (detached)
docker compose up -d

# Wait for services to become healthy
docker compose ps
```

### Pull Required Ollama Models (First Run Only)

```bash
make pull-models
# Pulls: qwen:7b, nomic-embed-text, llama3-router
```

Or manually:

```bash
docker compose exec ollama ollama pull qwen:7b
docker compose exec ollama ollama pull nomic-embed-text
```

### Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | `http://localhost` | React dashboard |
| API Docs | `http://localhost/api/docs` | Swagger UI |
| Prometheus | `http://localhost:9090` | Metrics scraper |
| Grafana | `http://localhost:3000` | Monitoring dashboard |
| Ollama | `http://localhost:11434` | (optional direct access) |

### Useful Commands

```bash
make logs           # Tail all service logs
make ps             # Show container health status
make shell-backend  # Open shell inside backend
make shell-ollama   # Open shell inside Ollama
make down           # Stop all services
make clean          # Remove all containers, volumes, images (destructive!)
```

---

## Development Mode (Hot Reload)

```bash
# Start with dev overrides (hot-reload backend, debug logging)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or run backend locally (no Docker)
python -m venv venv
source venv/Scripts/activate     # Windows
# source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend locally
cd frontend
npm install
npm run dev  # http://localhost:5173
```

---

## AMD ROCm GPU Acceleration

To enable GPU passthrough for the Ollama container:

1. Edit `docker-compose.yml`
2. Uncomment the `devices`, `group_add`, and `environment` blocks under the `ollama` service:

```yaml
ollama:
  # ...
  devices:
    - /dev/kfd
    - /dev/dri
  group_add:
    - video
    - render
  environment:
    - HSA_OVERRIDE_GFX_VERSION=11.0.0   # Set for your GPU
```

3. Find your GFX version:
```bash
rocminfo | grep "gfx"
```

4. Restart the Ollama service:
```bash
docker compose restart ollama
```

---

## Production Hardening Checklist

Before going to production, verify:

- [ ] `DEBUG=false` in `.env`
- [ ] `GRAFANA_ADMIN_PASSWORD` changed from default
- [ ] `API_KEY_ENABLED=true` with a strong `API_KEY` (if exposing publicly)
- [ ] `CORS_ORIGINS` restricted to your actual domains
- [ ] Nginx is configured with HTTPS (TLS termination)
- [ ] `.env` is in `.gitignore` and never committed
- [ ] Docker containers run as non-root (default in our Dockerfile)
- [ ] Named volumes are backed up regularly

---

## Scaling Considerations

The current setup uses SQLite, which limits concurrent write throughput. For high-traffic production:

1. **Migrate to PostgreSQL**: Replace `DATABASE_URL` with a PostgreSQL connection string and update `database.py` to use SQLAlchemy async engine.
2. **Horizontal backend scaling**: Switch to multiple Uvicorn workers behind a load balancer. SQLite must be replaced first.
3. **Redis-backed rate limiting**: Set `REDIS_URL` and configure slowapi to use Redis storage for distributed rate limiting.

---

## Monitoring Access

### Prometheus

```
URL: http://localhost:9090
Default targets: backend:8000/metrics (scraped every 10s)
Retention: 15 days
```

### Grafana

```
URL: http://localhost:3000
Username: admin
Password: (set via GRAFANA_ADMIN_PASSWORD env var)
Pre-loaded dashboard: "AMD Multi-Model Router"
```

---

## Backup & Recovery

### SQLite Database

```bash
# Backup
docker compose exec backend cp /app/data/metrics.db /app/data/metrics.db.bak

# Restore
docker compose exec backend cp /app/data/metrics.db.bak /app/data/metrics.db
```

### Ollama Models

Models are stored in the `amd_router_ollama_models` named volume. To backup:

```bash
docker run --rm \
  -v amd_router_ollama_models:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/ollama_models.tar.gz /data
```
