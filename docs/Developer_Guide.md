# Developer Guide

## Local Setup

### Requirements

- Python 3.11+
- Node.js 20+ and npm
- Docker Desktop (for running Ollama)
- Git

### Backend Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/your-org/AMD-Hackathon.git
cd AMD-Hackathon

# 2. Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows PowerShell
# source venv/bin/activate     # Linux/Mac

# 3. Install all dependencies (production + dev)
pip install -r requirements.txt -r requirements-dev.txt

# 4. Copy and configure .env
cp .env.example .env
# Edit .env: set FIREWORKS_API_KEY and OLLAMA_URL=http://localhost:11434

# 5. Initialise the database
python scripts/init_db.py

# 6. Start Ollama (Docker)
docker run -d -p 11434:11434 ollama/ollama
docker exec <ollama_container> ollama pull qwen:7b
docker exec <ollama_container> ollama pull nomic-embed-text

# 7. Start the FastAPI server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API available at:** `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Frontend available at: http://localhost:5173
```

---

## Code Quality

### Running Linters

```bash
# Format check (black)
black --check .

# Fix formatting in place
black .

# Import order check (isort)
isort --check .
isort .

# Lint and style (ruff)
ruff check .
ruff check --fix .
```

### Running Tests

```bash
# Full test suite with coverage
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run specific test file
pytest tests/unit/test_router.py -v

# Coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Type Checking

```bash
mypy app/
```

---

## Project Structure

```
AMD-Hackathon/
├── app/                    FastAPI backend
│   ├── config.py           Pydantic Settings (type-safe config)
│   ├── database.py         SQLite layer (context manager pattern)
│   ├── main.py             App entrypoint, middleware, routes
│   ├── models.py           Pydantic request/response schemas
│   ├── middleware/
│   │   └── logging_middleware.py   Structured JSON request logging
│   └── services/
│       ├── classifier.py   3-tier task classifier
│       ├── executor.py     Model execution + fallback chain
│       ├── fireworks_client.py     Fireworks API client
│       ├── ollama_client.py        Ollama API client + VRAM manager
│       └── router.py       Routing rules engine
│
├── ml/                     ML pipeline (classifier training)
│   ├── pipeline.py         Click CLI orchestrator
│   ├── registry.py         JSON model registry
│   └── stages/
│       ├── data_validation.py
│       ├── preprocessing.py
│       └── training.py     MLflow-tracked training
│
├── tests/                  Test suite
│   ├── conftest.py         Shared fixtures (mocked clients, temp DB)
│   ├── unit/               Unit tests (no external deps)
│   └── integration/        API integration tests
│
├── configs/                Externalized configuration
│   ├── routing_rules.yaml  Model routing + pricing config
│   └── model_registry.yaml HuggingFace + Ollama model mappings
│
├── monitoring/             Observability stack
│   ├── prometheus.yml      Scrape config
│   └── grafana/
│       └── provisioning/   Auto-loaded dashboards + datasources
│
├── docs/                   Production documentation
├── scripts/                Utility scripts
├── data/                   Runtime data (gitkeep only)
├── .github/workflows/      CI/CD pipelines
├── docker-compose.yml      Production compose
├── docker-compose.dev.yml  Dev hot-reload override
└── pyproject.toml          Tool configuration (black, ruff, pytest)
```

---

## Adding a New Task Category

1. **Update `configs/routing_rules.yaml`** — add new category entry
2. **Update `app/services/router.py`** — add to `routing_rules` dict
3. **Update `app/services/classifier.py`** — add regex keywords
4. **Update `scripts/generate_dataset.py`** — add seed prompts
5. **Update `CATEGORIES`** in `ml/stages/data_validation.py` and `preprocessing.py`
6. **Add test cases** in `tests/unit/test_classifier.py` and `test_router.py`
7. **Regenerate the dataset** and retrain: `python -m ml.pipeline run`

---

## Environment Variables Reference

See `.env.example` for the full list. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FIREWORKS_API_KEY` | (required) | Cloud model API key |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama service URL |
| `RATE_LIMIT_PER_MINUTE` | `30` | Requests per IP per minute |
| `API_KEY_ENABLED` | `false` | Enable API key auth |
| `PROMETHEUS_ENABLED` | `true` | Expose /metrics endpoint |
| `MLFLOW_TRACKING_URI` | `./mlruns` | MLflow server URI |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DEBUG` | `false` | Debug mode |

---

## Making a Release

```bash
# 1. Update version in app/main.py (version= parameter)
# 2. Commit all changes
git add .
git commit -m "chore: bump version to v1.2.0"

# 3. Tag the release (triggers Docker build workflow)
git tag v1.2.0
git push origin main --tags

# 4. GitHub Actions will:
#    - Run linting + tests
#    - Build Docker images
#    - Push to GitHub Container Registry with :v1.2.0 and :latest tags
```

---

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check container health
docker compose ps
docker compose logs ollama
```

### Database errors
```bash
# Reinitialise (won't delete data, just re-creates missing tables)
python scripts/init_db.py
```

### ChromaDB collection issues
```bash
# Reset ChromaDB (will reseed on next startup)
rm -rf data/chromadb/
docker compose restart backend
```

### Tests failing
```bash
# Run with verbose output
pytest tests/ -v --tb=long

# Check that DATABASE_FILE env var is set for tests
export DATABASE_FILE=/tmp/test.db
pytest tests/
```
