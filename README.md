# SLM-Based Intelligent Multi-Model Routing System

[![CI](https://github.com/your-org/AMD-Hackathon/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/AMD-Hackathon/actions/workflows/ci.yml)
[![Docker](https://github.com/your-org/AMD-Hackathon/actions/workflows/docker-build.yml/badge.svg)](https://github.com/your-org/AMD-Hackathon/actions/workflows/docker-build.yml)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)

An intelligent, self-resilient API routing gateway designed for the **AMD Developer Hackathon (Track 1)**. Optimises token efficiency and API costs by dynamically directing queries to local Small Language Models (SLMs) running on AMD ROCm hardware or falling back to cloud models.

---

## 🚀 Key Features

1. **3-Tier Hybrid Classification Engine**
   - *Tier 1 (Fine-tuned SLM):* QLoRA-tuned Llama-3.2-1B router model
   - *Tier 2 (Vector Search):* ChromaDB + `nomic-embed-text` semantic classification
   - *Tier 3 (Regex Fallback):* Keyword rules — 100% uptime guarantee

2. **Intelligent Model Routing** — task-specific model dispatch with auto-fallback
3. **Cost Tracking & Savings Analytics** — real-time cost vs. baseline dashboard
4. **Production Monitoring** — Prometheus metrics + Grafana dashboards
5. **Experiment Tracking** — MLflow for classifier training pipeline
6. **Rate Limiting & Security** — configurable per-IP rate limiting, optional API key auth

---

## 📊 Model Routing Table

| Task | Primary Model | Fallback | Purpose |
|------|--------------|---------|---------|
| **Coding** | `kimi-k2p7-code` | `gemma-4-31b-it` | Specialized code generation |
| **Math** | `gemma-4-31b-it` | `gemma-4-31b-it-nvfp4` | High-precision reasoning |
| **Research** | `gemma-4-26b-a4b-it` | `gemma-4-31b-it` | Summarization & extraction |
| **Casual Chat** | `minimax-m3` | `gemma-4-26b-a4b-it` | Fast conversational queries |

---

## 📂 Project Structure

```
AMD-Hackathon/
├── app/                        FastAPI backend
│   ├── Dockerfile              Multi-stage, non-root production image
│   ├── config.py               Pydantic Settings (type-safe, validated)
│   ├── database.py             SQLite logging + metrics
│   ├── main.py                 Routes, CORS, rate limiting, Prometheus
│   ├── models.py               Pydantic schemas + validators
│   ├── middleware/
│   │   └── logging_middleware.py   Structured JSON request logging
│   └── services/
│       ├── classifier.py       3-tier classifier
│       ├── executor.py         Model execution + fallback chain
│       ├── ollama_client.py    Ollama + VRAM manager
│       ├── fireworks_client.py Fireworks cloud client
│       └── router.py           Routing rules engine
│
├── ml/                         ML pipeline (classifier training)
│   ├── pipeline.py             Click CLI: validate→preprocess→train→register
│   ├── registry.py             JSON model version registry
│   └── stages/                 Individual pipeline stage modules
│
├── tests/                      Full test suite
│   ├── conftest.py             Fixtures with mocked services
│   ├── unit/                   Unit tests (no external deps)
│   └── integration/            API integration tests
│
├── monitoring/                 Prometheus + Grafana
│   ├── prometheus.yml          Scrape configuration
│   └── grafana/provisioning/   Pre-loaded dashboards + datasources
│
├── configs/                    Externalized YAML configs
│   ├── routing_rules.yaml      Model assignments + pricing
│   └── model_registry.yaml     HuggingFace model mappings
│
├── docs/                       Production documentation
│   ├── Architecture.md
│   ├── API.md
│   ├── MLOps.md
│   ├── Deployment.md
│   └── Developer_Guide.md
│
├── scripts/                    Utility scripts
├── frontend/                   React + Vite SPA
├── data/                       Runtime data (gitkeep)
├── .github/workflows/          CI/CD pipelines
├── docker-compose.yml          Production (includes Prometheus + Grafana)
├── docker-compose.dev.yml      Dev hot-reload override
├── pyproject.toml              Tool config (black, ruff, pytest)
└── Makefile                    Developer convenience targets
```

---

## 🐳 Docker Quick Start (Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose)
- A [Fireworks AI](https://fireworks.ai) API key

### 1. Configure environment
```bash
cp .env.example .env
# Edit .env: set FIREWORKS_API_KEY and GRAFANA_ADMIN_PASSWORD
```

### 2. Build and start all services
```bash
make build
make up
```

### 3. Pull Ollama models (first run only)
```bash
make pull-models
```

### 4. Access the services

| Service | URL |
|---------|-----|
| 🖥️ React Dashboard | `http://localhost` |
| 📖 API Docs (Swagger) | `http://localhost/api/docs` |
| 📊 Prometheus | `http://localhost:9090` |
| 📈 Grafana | `http://localhost:3000` (admin/admin) |
| 🤖 Ollama | `http://localhost:11434` |

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run full test suite with coverage
make test
# or: pytest tests/ -v --cov=app

# Run linting
make lint

# Auto-format code
make format
```

---

## 🤖 ML Pipeline

```bash
# Generate synthetic training data
make generate-dataset

# Run full pipeline (validate → preprocess → train → register)
make pipeline

# View registered model versions
make pipeline-list

# Start MLflow UI
make mlflow-ui  # → http://localhost:5000
```

---

## 🛠️ Local Development (without Docker)

```bash
# Backend
python -m venv venv && source venv/Scripts/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # set OLLAMA_URL=http://localhost:11434
make dev-backend       # → http://localhost:8000

# Frontend
cd frontend && npm install && npm run dev  # → http://localhost:5173
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Architecture.md](docs/Architecture.md) | System design, components, data flow |
| [API.md](docs/API.md) | Endpoint reference, request/response schemas |
| [MLOps.md](docs/MLOps.md) | ML pipeline, MLflow tracking, model registry |
| [Deployment.md](docs/Deployment.md) | Docker setup, AMD ROCm, production checklist |
| [Developer_Guide.md](docs/Developer_Guide.md) | Local setup, code quality, contributing |

---

## 🔒 Security

- Input validation: prompt length 5–8000 chars, valid task_type enum
- Rate limiting: configurable per-IP (default: 30 req/min)
- Optional API key authentication (`X-API-Key` header)
- Non-root Docker container
- Secrets via environment variables only — never hardcoded

---

## 👥 Team

| Role | Responsibility |
|------|---------------|
| **Lead Architect & GPU VRAM Systems** | ROCm memory hooks, dynamic model loader, SQLite backend |
| **Task Classifier & NLP Engine** | ChromaDB, embeddings, regex fallback |
| **Model Integrations & ROCm Tuning** | HuggingFace pipelines, quantisation, token tracking |
| **Frontend, Analytics & QA** | React dashboard, metrics charts, test suite |
