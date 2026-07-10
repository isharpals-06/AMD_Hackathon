# SLM-Based Intelligent Multi-Model Routing System

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An intelligent, self-resilient API routing gateway designed for the **AMD Developer Hackathon**. Optimises token efficiency, latency, and API costs by dynamically directing queries to local Small Language Models (SLMs) running on GPU hardware or cascading to high-capacity cloud models.

---

## 🚀 Key Features

1. **3-Tier Hybrid Classification Engine**
   - *Tier 1 (Fine-tuned SLM):* QLoRA-tuned Llama-3.2-1B router model (`llama3-router` in Ollama).
   - *Tier 2 (Vector Search):* ChromaDB semantic similarity match via `nomic-embed-text` embeddings.
   - *Tier 3 (Regex Fallback):* Keyword word-boundary regex rules — guarantees 100% classification uptime.

2. **Intelligent Model Routing** — Task-specific model dispatch with automatic cloud fallback using the Hugging Face unified completions API.
3. **Cost Tracking & Savings Analytics** — Real-time cost vs. baseline calculation displayed on a React/Vite dashboard.
4. **Concurrent Write Lock-Free Database** — SQLite backend configured with Write-Ahead Logging (WAL) and 30s timeouts for high concurrent write safety.
5. **Experiment Tracking** — MLflow integration for model pipeline validation, preprocessing, training, and registration.
6. **Windows Helper Launcher** — One-click batch setup (`run.bat`) to orchestrate Ollama, Backend FastAPI, and React Frontend automatically.

---

## 📊 Model Routing & Fallback Table

Model routing rules are externalized in `configs/routing_rules.yaml`. You can override these mappings dynamically in `.env` to enforce specific model targets:

| Task Type | Primary Model (Cloud) | Fallback Model (Cloud / Local) | Purpose |
|:---|:---|:---|:---|
| **Coding** | `Qwen/Qwen2.5-Coder-32B-Instruct` | `Qwen/Qwen2.5-Coder-7B-Instruct` | Advanced code gen and refactoring |
| **Math** | `Qwen/Qwen2.5-72B-Instruct` | `meta-llama/Llama-3.1-8B-Instruct` | Multi-step mathematical reasoning |
| **Research** | `meta-llama/Llama-3.1-8B-Instruct` | `Qwen/Qwen2.5-7B-Instruct` | Summarization, analysis, extraction |
| **Casual Chat** | `Qwen/Qwen2.5-7B-Instruct` | `Qwen/Qwen2.5-7B-Instruct` | Fast conversational responses |

---

## 📂 Project Structure

```
AMD-Hackathon/
├── app/                        FastAPI backend application
│   ├── config.py               Pydantic Settings with env parsing
│   ├── database.py             SQLite connection (WAL mode enabled) + metrics aggregation
│   ├── main.py                 API router routes, rate limiting, and dashboard endpoints
│   ├── models.py               Request/Response validation schemas
│   └── services/
│       ├── classifier.py       3-tier classifier engine (robust JSON + AST fallbacks)
│       ├── executor.py         Model execution client + fallback fallback logic
│       ├── huggingface_client.py Hugging Face serverless unified completions API
│       ├── ollama_client.py    Local Ollama API client
│       └── router.py           Routing configurations and cost calculation engine
│
├── ml/                         ML classification pipeline (MLflow)
│   ├── pipeline.py             Click CLI: validate → preprocess → train → register
│   ├── registry.py             JSON-based local model registry index
│   └── stages/                 ML pipeline execution stages
│
├── frontend/                   Vite + React SPA dashboard
│   ├── src/                    Components, charts, and pages
│   └── vite.config.js          Proxy settings to API backend
│
├── configs/                    YAML configuration rules
│   └── routing_rules.yaml      Model pricing and routing targets
│
├── docs/                       System documentation
│   └── conversation_continuation.md State document for next team/session handoff
│
├── scripts/                    Developer utility scripts
│   ├── build_router.py         Registers fine-tuned adapter into Ollama Modelfile
│   ├── generate_dataset.py     Generates synthetic dataset (dynamic count and seeds)
│   └── seed_data.py            Seeds ChromaDB with demonstration prompts
│
├── tests/                      Pytest suite
│   ├── unit/                   Unit tests
│   └── test_classifier.py      Classifier tests isolated from env overrides
│
├── run.bat                     Windows one-click consolidated startup script
└── requirements.txt            Backend dependencies
```

---

## ⚡ Windows Quick Start (Recommended)

### 1. Prerequisites
- Python 3.11+
- Node.js (v18+)
- [Ollama for Windows](https://ollama.com/) (Make sure it is installed and running)
- Hugging Face API Token (configured in `.env`)

### 2. Install Dependencies
Run the following in your terminal to set up the virtual environment:
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt -r requirements-dev.txt

# Install frontend modules
cd frontend
npm install
cd ..
```

### 3. Configure `.env` File
Create a `.env` file in the root directory:
```env
DEBUG=True
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_ROUTER_MODEL=llama3-router
HF_TOKEN=your_huggingface_token_here

# Cloud endpoints configuration
MATH_PRIMARY_MODEL=huggingface:Qwen/Qwen2.5-72B-Instruct
MATH_FALLBACK_MODEL=huggingface:meta-llama/Llama-3.1-8B-Instruct
CODING_PRIMARY_MODEL=huggingface:Qwen/Qwen2.5-Coder-32B-Instruct
CODING_FALLBACK_MODEL=huggingface:Qwen/Qwen2.5-Coder-7B-Instruct
RESEARCH_PRIMARY_MODEL=huggingface:meta-llama/Llama-3.1-8B-Instruct
RESEARCH_FALLBACK_MODEL=huggingface:Qwen/Qwen2.5-7B-Instruct
CASUAL_PRIMARY_MODEL=huggingface:Qwen/Qwen2.5-7B-Instruct
CASUAL_FALLBACK_MODEL=huggingface:Qwen/Qwen2.5-7B-Instruct
```

### 4. Consolidated Startup
Double-click `run.bat` or run:
```powershell
./run.bat
```
This automatically launches Ollama, the FastAPI backend on `http://localhost:8000`, and the React Frontend on `http://localhost:5173`.

---

## 🧪 Seeding & Validation

### 1. Seed ChromaDB for Demo
Once the backend is running, seed ChromaDB with 30 high-quality demo prompts:
```powershell
$env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python scripts/seed_data.py
```

### 2. Run Failover Simulation Checks
Verify that the model executor cascades cleanly from primary models to fallbacks when a cloud API goes down:
```powershell
$env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python scratch/test_failover.py
```

### 3. Run SQLite Concurrency Stress Test
Run a concurrent write test (150 parallel inserts) to verify the database WAL lock-free architecture:
```powershell
.venv\Scripts\python scratch/stress_test_db.py
```

---

## 🧠 ML training Pipeline (MLflow)

You can generate fresh datasets and re-train the classification model dynamically:

```powershell
# 1. Generate a fresh, larger training dataset (e.g. 5,000 prompts)
$env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python scripts/generate_dataset.py --num 5000

# 2. Run the ML pipeline (Validation -> Preprocessing -> LogReg Training -> Production Registry Promotion)
$env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python -m ml.pipeline run --data-path ./data/training_dataset.csv --version 1.1.0 --auto-promote

# 3. View the MLflow UI
.venv\Scripts\mlflow ui
```

---

## 🔬 Testing & Quality Control

### Run Automated Tests
```powershell
.venv\Scripts\pytest -v
```
All **84/84 tests** pass cleanly with 76.48% coverage.

### Verify Code Formatting
```powershell
.venv\Scripts\black . --check
```

---

## 👥 Hackathon Team Assignment

* **💻 Frontend Developer (Teammate):** Dashboard styling, screenshots, playground validations, and demo video screen recording.
* **🗄️ Database, Testing & Stress Testing (User):** SQLite WAL mode, concurrency testing, logging transactions.
* **🧠 Model & ML Engineer (User):** Ollama Modelfile registration, model-swapping optimization, MLflow training pipeline.
* **⚙️ DevOps & Integration (Teammate):** Startup orchestrator batch scripts (`run.bat`), failover simulations, remote GitHub deployments.
