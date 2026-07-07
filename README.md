# SLM-Based Intelligent Multi-Model Routing System

An intelligent, self-resilient API routing gateway designed for the **AMD Developer Hackathon (Track 1)**. This project optimizes token efficiency and minimises API costs by dynamically directing queries to local Small Language Models (SLMs) running on AMD hardware or falling back to powerful cloud models.

---

## 🚀 Key Features

1. **Semantic Task Classifier (Local Vector DB):** Utilises an in-memory **ChromaDB** database seeded with prompt examples. User prompts are embedded using `nomic-embed-text` via Ollama and classified semantically into domains (Math, Coding, Research, or Casual Chat).
2. **Robust Regex Fallback:** If the vector DB or embedding service is down, the system gracefully falls back to keyword-based regex rules for 100% classification uptime.
3. **Hybrid Model Execution:**
    *   **Math Tasks:** Routed to cloud-based `Qwen-72B` (via Fireworks API).
    *   **Coding/Code Review Tasks:** Routed to cloud-based `Mixtral 8x7B` (via Fireworks API).
    *   **Research (RAG) Tasks:** Routed to `Mixtral 8x7B` (with fallback to local Qwen 7B).
    *   **Casual Chat Tasks:** Routed to a local, free `Qwen 7B` model (via Ollama).
4. **Automatic Fallback Chain:** If the primary model fails or times out, the router retries using a secondary model automatically.
5. **Performance & Savings Logger (SQLite):** Writes transaction latencies, exact token usage, and cost stats to SQLite to compute real-time cost-savings metrics.

---

## 📂 Project Structure

```
AMD-Hackathon/
├── docker-compose.yml          # Orchestrates backend + frontend + Ollama
├── Makefile                    # Developer convenience targets
├── .env.example                # Environment variable template
├── .dockerignore
├── .gitignore
├── requirements.txt            # Python backend dependencies
├── Modelfile                   # Ollama local model build template for QLoRA
│
├── app/                        # FastAPI backend
│   ├── Dockerfile
│   ├── main.py                 # API entrypoint (lifespan, /process, /metrics, /health)
│   ├── config.py               # Env-based configuration
│   ├── models.py               # Pydantic request/response schemas
│   ├── database.py             # SQLite logging & metrics aggregation
│   └── services/
│       ├── classifier.py       # 3-tier classifier (SLM → ChromaDB → Regex)
│       ├── router.py           # Routing rule engine
│       ├── executor.py         # Model execution + fallback chain
│       ├── ollama_client.py    # Ollama API client
│       └── fireworks_client.py # Fireworks API client
│
├── frontend/                   # React + Vite SPA
│   ├── Dockerfile              # Multi-stage: node:20 build → nginx:alpine serve
│   ├── nginx.conf              # SPA routing + /api/ proxy → backend
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── App.jsx             # App shell with sidebar navigation
│       ├── pages/
│       │   ├── HomePage.jsx    # Dashboard overview + routing table
│       │   ├── PlaygroundPage.jsx  # Interactive prompt tester
│       │   └── MetricsPage.jsx     # Charts + aggregated stats
│       ├── components/
│       │   ├── dashboard/
│       │   ├── playground/
│       │   └── ui/
│       ├── services/
│       │   ├── api.js          # Fetch wrapper (uses /api/ proxy in prod)
│       │   └── metrics.js
│       ├── hooks/
│       └── utils/
│
├── scripts/
│   ├── notebook_code.py        # Clean Python cells for Jupyter notebook
│   ├── init_db.py              # SQLite table initialiser
│   ├── merge_lora.py           # LoRA weight merging (optional)
│   ├── generate_dataset.py     # Synthetic dataset generator (2000 rows)
│   ├── cache_models.py         # Pre-cache Ollama models
│   └── health_check.py         # Standalone health checker
│
├── data/                       # Runtime data (git-tracked as placeholder)
│   └── .gitkeep                # metrics.db and chromadb/ created at runtime
│
└── Documentation/
    ├── PRD.md
    ├── TDD.md
    ├── Setup_Guide.md
    ├── Test_Plan.md
    └── Team_Allocation.md
```

---

## 🐳 Docker Quick Start (Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose plugin)
- A Fireworks API key → [fireworks.ai](https://fireworks.ai)

### 1. Configure environment
```bash
cp .env.example .env
# Edit .env and set FIREWORKS_API_KEY=your_key_here
```

### 2. Build and start all services
```bash
make build
make up
# or without Make:
# docker compose build && docker compose up -d
```

### 3. Pull the required Ollama models (first run only)
```bash
make pull-models
# Pulls: qwen:7b, nomic-embed-text, llama3-router
```

### 4. Open the dashboard
```
http://localhost        ← React frontend (Nginx)
http://localhost/api/docs   ← FastAPI Swagger UI (via proxy)
http://localhost:11434  ← Ollama (optional direct access)
```

### Useful commands
```bash
make logs           # Tail logs from all services
make ps             # Show container health status
make shell-backend  # Open shell inside backend container
make down           # Stop all services
make clean          # Remove all containers, volumes, and images
```

### AMD ROCm GPU Passthrough
To enable AMD GPU acceleration inside the Ollama container, uncomment the `devices` and `group_add` block in `docker-compose.yml` and set `HSA_OVERRIDE_GFX_VERSION` for your GPU.

---

## 🛠️ Local Development (without Docker)

### 1. Backend
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # set OLLAMA_URL=http://localhost:11434
make dev-backend           # or: uvicorn app.main:app --reload
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev                # Vite dev server on http://localhost:5173
```

### 3. Database initialisation
```bash
python scripts/init_db.py
```

---

## 👥 Team Roles (4-Person Restructure)

*   **Person 1: Lead Architect & GPU VRAM Systems** — Configures PyTorch memory hooks on ROCm, manages the dynamic model loader/unloader, and maintains the SQLite logging backend.
*   **Person 2: Task Classifier & NLP Engine** — Sets up the ChromaDB instance, integrates local embedding encoders, and manages regex fallback rules.
*   **Person 3: Model Integrations & ROCm Tuning** — Integrates HuggingFace model pipelines, tunes quantisation/precision for local models, and tracks tokens.
*   **Person 4: Frontend UI, Analytics Dashboard & QA** — Builds the React dashboard, compiles metric summaries, executes the test suite, and conducts benchmarking checks for final submission.
