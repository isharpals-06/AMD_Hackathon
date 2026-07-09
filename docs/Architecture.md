# Architecture Overview

## System Design

The AMD Multi-Model Router is a **production-grade, cost-optimized LLM routing gateway** designed for AMD ROCm GPUs. It dynamically classifies incoming prompts and routes them to the most appropriate model — local (via Ollama) or cloud (via Fireworks AI) — with automatic fallback, cost tracking, and full observability.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Client / Browser                                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │ HTTP (port 80)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Nginx (React SPA + API Proxy)                          │
│   Serves static React bundle │ Proxies /api/* → backend:8000            │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │ HTTP internal (router_net)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                            │
│                                                                           │
│  ┌──────────────────┐   ┌─────────────────┐   ┌──────────────────────┐  │
│  │  Rate Limiter    │   │  CORS Middleware │   │  Structured Logging  │  │
│  │  (slowapi)       │   │  (configurable)  │   │  (JSON per request)  │  │
│  └──────────────────┘   └─────────────────┘   └──────────────────────┘  │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    3-Tier Task Classifier                         │    │
│  │   Tier 1: Fine-tuned Llama-3.2-1B SLM (via Ollama)              │    │
│  │        ↓ (on failure)                                            │    │
│  │   Tier 2: ChromaDB Vector Search (nomic-embed-text embeddings)   │    │
│  │        ↓ (on failure)                                            │    │
│  │   Tier 3: Keyword Regex Fallback                                 │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│                              ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                     Routing Engine                                │    │
│  │   math      → gemma-4-31b-it  (fallback: gemma-4-31b-it-nvfp4)  │    │
│  │   coding    → kimi-k2p7-code  (fallback: gemma-4-31b-it)        │    │
│  │   research  → gemma-4-26b-a4b (fallback: gemma-4-31b-it)        │    │
│  │   chat      → minimax-m3      (fallback: gemma-4-26b-a4b)       │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│               ┌──────────────┴─────────────┐                             │
│               ▼                             ▼                             │
│  ┌────────────────────┐      ┌────────────────────────┐                  │
│  │  Ollama Client     │      │  Fireworks Client      │                  │
│  │  (local AMD GPU)   │      │  (cloud fallback)      │                  │
│  └────────────────────┘      └────────────────────────┘                  │
│               │                             │                             │
│               └──────────────┬─────────────┘                             │
│                              ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │           SQLite Metrics Logger + Response Assembly              │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
         │ Prometheus /metrics                   │ Ollama API (port 11434)
         ▼                                       ▼
┌──────────────────┐                  ┌──────────────────────────────────┐
│   Prometheus     │ ────scrapes───▶  │  Ollama Container                │
│   (port 9090)    │                  │  AMD ROCm GPU Models             │
└──────────────────┘                  └──────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│   Grafana        │
│   (port 3000)    │
└──────────────────┘
```

---

## Component Descriptions

### Frontend — React + Vite (Nginx)
- **Tech**: React 18, Vite, served by Nginx
- **Pages**: Home/Dashboard, Playground (interactive prompt tester), Metrics charts
- **API**: Proxies all `/api/*` requests to the FastAPI backend
- **Port**: 80 (public)

### Backend — FastAPI
- **Tech**: Python 3.11, FastAPI, Uvicorn, Pydantic Settings
- **Key middleware**: CORS, request-ID logging, rate limiting (slowapi)
- **Endpoints**: `/process`, `/health`, `/version`, `/metrics/summary`, `/metrics/models`, `/metrics` (Prometheus)
- **Port**: 8000 (internal only in production)

### 3-Tier Classifier
| Tier | Method | Trigger |
|------|--------|---------|
| **1** | Fine-tuned Llama-3.2-1B SLM (QLoRA) | Always first |
| **2** | ChromaDB vector search + nomic-embed-text | If Tier 1 fails |
| **3** | Keyword regex rules | If Tier 2 fails |

### Ollama
- Hosts all local model inference (AMD ROCm or CPU)
- VRAM management: models are explicitly swapped using `keep_alive=0`
- Port: 11434 (internal + optional external)

### Monitoring Stack
- **Prometheus**: scrapes `/metrics` every 10s, retains 15 days
- **Grafana**: pre-loaded dashboard with latency, error rate, throughput panels

### ML Pipeline
- **CLI**: `python -m ml.pipeline run`
- **Stages**: validate → preprocess → train (MLflow) → register
- **Tracking**: MLflow with local `./mlruns` backend (configurable)
- **Registry**: JSON-based at `models/registry.json`

---

## Data Flow — Single Request

```
1. Client POSTs prompt to /process
2. Rate limiter checks IP allowance
3. (Optional) API key validation
4. Classifier assigns task_type (math/coding/research/casual_chat)
5. RoutingEngine returns primary + fallback model config
6. ModelExecutor calls primary model via OllamaClient
   → If timeout/error: calls fallback model
   → If both fail: returns HTTP 500
7. Response assembled with tokens, cost, latency metadata
8. Request logged to SQLite (async, best-effort)
9. Response returned to client
10. Prometheus records metrics (handled by instrumentator middleware)
```

---

## Security Model

| Concern | Implementation |
|---------|---------------|
| API authentication | Optional `X-API-Key` header (toggle via `API_KEY_ENABLED`) |
| CORS | Configurable allowlist via `CORS_ORIGINS` env var |
| Rate limiting | Per-IP, configurable `RATE_LIMIT_PER_MINUTE` |
| Input validation | Pydantic: min 5 chars, max 8000 chars, valid task_type enum |
| Secrets | Never hardcoded; loaded from `.env` via Pydantic Settings |
| Container user | Non-root `appuser` in Docker runtime stage |

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| API Framework | FastAPI | ≥0.111 |
| Config | Pydantic Settings | ≥2.3 |
| HTTP Client | httpx | ≥0.27 |
| Database | SQLite (via stdlib) | built-in |
| Vector DB | ChromaDB | ≥0.5 |
| Rate Limiting | slowapi | ≥0.1.9 |
| Metrics | prometheus-fastapi-instrumentator | ≥7.0 |
| Logging | python-json-logger | ≥2.0 |
| ML Tracking | MLflow | ≥2.13 |
| Frontend | React 18 + Vite | — |
| Container | Docker + Compose | — |
| CI/CD | GitHub Actions | — |
