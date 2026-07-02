# SLM-Based Intelligent Multi-Model Routing System

An intelligent, self-resilient API routing gateway designed for the **AMD Developer Hackathon (Track 1)**. This project optimizes token efficiency and minimizes API costs by dynamically directing queries to local Small Language Models (SLMs) running on AMD hardware or falling back to powerful cloud models.

---

## 🚀 Key Features

1.  **Semantic Task Classifier (Local Vector DB):** Utilizes an in-memory **ChromaDB** database seeded with prompt examples. User prompts are embedded using `nomic-embed-text` via Ollama and classified semantically into domains (Math, Coding, Research, or Casual Chat).
2.  **Robust Regex Fallback:** If the vector DB or embedding service is down, the system gracefully falls back to keyword-based regex rules for 100% classification uptime.
3.  **Hybrid Model Execution:**
    *   **Math Tasks:** Routed to cloud-based `Qwen-72B` (via Fireworks API).
    *   **Coding/Code Review Tasks:** Routed to cloud-based `Mixtral 8x7B` (via Fireworks API).
    *   **Research (RAG) Tasks:** Routed to `Mixtral 8x7B` (with fallback to local Qwen 7B).
    *   **Casual Chat Tasks:** Routed to a local, free `Qwen 7B` model (via Ollama).
4.  **Automatic Fallback Chain:** If the primary model fails or times out, the router retries using a secondary model automatically.
5.  **Performance & Savings Logger (SQLite):** Writes transaction latencies, exact token usage, and cost stats to SQLite to compute real-time cost-savings metrics.

---

## 📂 Project Structure

```
multi-model-router/
├── app/
│   ├── main.py                 # FastAPI application routes (/process, /metrics, /health)
│   ├── config.py               # Settings and configuration loader (.env)
│   ├── database.py             # SQLite database operations and aggregates
│   ├── models.py               # Pydantic schemas for requests/responses/errors
│   └── services/
│       ├── classifier.py       # ChromaDB vector search & regex fallback classifier
│       ├── executor.py         # Multi-model execution and retry orchestration
│       ├── router.py           # Model selection and token pricing rules
│       ├── ollama_client.py    # Local Ollama connection client
│       └── fireworks_client.py # Cloud Fireworks API connection client
├── Documentation/              # PRD, TDD, and Test cases
├── scripts/
│   ├── init_db.py              # SQLite database initializer
│   └── health_check.py         # Integration dependency checker
├── requirements.txt            # Python dependencies list
├── .env.example                # Example configuration template
└── .gitignore                  # Git ignore rules
```

---

## 🛠️ Getting Started

### 1. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```

### 3. Initialize the SQLite Database
```bash
python scripts/init_db.py
```

### 4. Run the Health Check
Verify Ollama models (`qwen:7b`, `nomic-embed-text`) and Fireworks connections are operational:
```bash
python scripts/health_check.py
```

### 5. Start the Server
Run the FastAPI application locally:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Access the interactive documentation at `http://localhost:8000/docs`.

---

## 👥 Team Roles (6-Person)

*   **Person 1: Backend/Router Architecture** - FastAPI setup and core router decision engine.
*   **Person 2: Task Classifier** - ChromaDB vector database setup and fallback regex logic.
*   **Person 3: Model Integrations** - Fireworks and Ollama API clients with token tracking.
*   **Person 4: Database & Metrics Logging** - SQLite database logging and cost aggregate metrics.
*   **Person 5: Frontend & Dashboard** - Web UI (React + Vite) dashboard and Click CLI tool.
*   **Person 6: QA, DevOps & Presentation** - Pytest suite, Docker Compose, benchmarking, and video/slides preparation.
