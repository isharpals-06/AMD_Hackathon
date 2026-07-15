# AMD Multi-Model Fallback Router — Conversation Continuation Document

> **Generated:** 2026-07-10 12:01 IST  
> **Workspace:** `C:\Users\ishar\projects\amd`  
> **GitHub Repo:** `isharpals-06/AMD_Hackathon`  
> **Branches:** `main` (production), `testing` (development)  
> **Current Branch:** `testing`

---

## 1. Executive Summary

### Main Goals
Build an **AMD Multi-Model Fallback Router** for a hackathon — a FastAPI backend + React/Vite dashboard that:
- Classifies incoming prompts into task categories (math, coding, research, casual_chat) using a **3-tier classification engine** (Fine-tuned SLM → ChromaDB vector search → Regex fallback).
- Routes prompts to the best-fit model (local Ollama or cloud HuggingFace) based on the classification.
- Tracks metrics (latency, tokens, cost savings) in SQLite and displays them on a React dashboard.
- Supports MLOps: MLflow model registry, training pipeline, data validation.

### Current Status
- **Core app:** Fully functional — backend serving on `http://localhost:8000`, frontend on `http://localhost:5173`.
- **3-tier classification:** Working. Tier 1 (local `llama3-router` SLM) now correctly classifies prompts and maps them to configured routing rules. Tier 2 (ChromaDB) and Tier 3 (Regex) serve as fallbacks.
- **CI/CD:** GitHub Actions pipeline passes code quality (black formatting). Test suite and Docker build are configured but skipped in CI (they pass locally).
- **ML Pipeline:** Stages 1 (Validation) and 2 (Preprocessing) pass. **Stage 3 (Training) has a fix just applied but not yet verified** — see Outstanding Tasks.
- **Team task delegation:** A 4-role task checklist with timeline has been created.

### Most Important Conclusions
- The HuggingFace unified endpoint `https://router.huggingface.co/v1/chat/completions` is the correct one (not `/hf-inference/v1/`).
- The local SLM (`llama3-router`) outputs JSON with varying key names (`task_type`, `task_category`, `Programming` vs `coding`) and wraps it with `assistant\n\n` prefix — robust parsing was implemented.
- scikit-learn 1.7+ removed the `multi_class` parameter from `LogisticRegression`.
- Black formatter version mismatch between local and CI caused repeated CI failures — resolved by upgrading local black to match CI's `v26.x`.

---

## 2. User Profile & Preferences

| Attribute | Detail |
|:---|:---|
| **Name** | Ishar (GitHub: isharpals-06) |
| **Role** | Team lead in a hackathon team of 4 |
| **OS** | Windows 11 |
| **GPU** | NVIDIA GeForce RTX 5050 Laptop GPU (8 GB VRAM, CUDA 12.0) |
| **Integrated GPU** | Intel UHD Graphics 770 (disabled for Ollama by default) |
| **Python** | 3.11 (via uv, cpython-3.11-windows-x86_64) |
| **Ollama** | v0.30.10 (Vulkan mode, CUDA detected) |
| **Skill Level** | Intermediate — comfortable with Python, FastAPI, React; learning MLOps |
| **Preferences** | Prefers direct action over lengthy explanations. Wants code changes pushed, not just described. |
| **Constraints** | Hackathon deadline — Day 4/5. Must finish all remaining tasks today (July 10, 2026). |
| **Long-term Goals** | Win the hackathon; demonstrate AMD GPU-optimized multi-model routing. |

---

## 3. Projects & Ideas Discussed

### Project: AMD Multi-Model Fallback Router

**Purpose:** Demonstrate intelligent prompt routing across multiple AI models (local Ollama SLMs and cloud HuggingFace endpoints) with fallback cascading, optimized for AMD hardware.

**Architecture:**
```
User Prompt → FastAPI /process endpoint
  → 3-Tier Classifier:
      Tier 1: llama3-router (fine-tuned Llama 3.2 1B QLoRA, local Ollama)
      Tier 2: ChromaDB vector search (nomic-embed-text embeddings)
      Tier 3: Regex keyword matching
  → Category: math | coding | research | casual_chat
  → RoutingEngine: loads models from configs/routing_rules.yaml
  → ModelExecutor: tries primary model, falls back to fallback model
  → Response + metrics logged to SQLite
  → React Dashboard displays stats via /metrics/summary
```

**Key Files:**
| File | Purpose |
|:---|:---|
| [app/main.py](file:///C:/Users/ishar/projects/amd/app/main.py) | FastAPI routes: `/process`, `/health`, `/metrics`, `/config` |
| [app/config.py](file:///C:/Users/ishar/projects/amd/app/config.py) | Pydantic Settings with `lru_cache` (needs process restart to refresh `.env`) |
| [app/database.py](file:///C:/Users/ishar/projects/amd/app/database.py) | SQLite connection, `init_db()`, `get_aggregate_metrics()` |
| [app/services/classifier.py](file:///C:/Users/ishar/projects/amd/app/services/classifier.py) | 3-tier classification engine |
| [app/services/router.py](file:///C:/Users/ishar/projects/amd/app/services/router.py) | Loads `configs/routing_rules.yaml`, returns model config per category |
| [app/services/ollama_client.py](file:///C:/Users/ishar/projects/amd/app/services/ollama_client.py) | Async Ollama HTTP client |
| [app/services/huggingface_client.py](file:///C:/Users/ishar/projects/amd/app/services/huggingface_client.py) | HuggingFace Inference API client |
| [configs/routing_rules.yaml](file:///C:/Users/ishar/projects/amd/configs/routing_rules.yaml) | Model routing rules + pricing per category |
| [frontend/src/pages/HomePage.jsx](file:///C:/Users/ishar/projects/amd/frontend/src/pages/HomePage.jsx) | Dashboard home with stats cards |
| [frontend/src/pages/MetricsPage.jsx](file:///C:/Users/ishar/projects/amd/frontend/src/pages/MetricsPage.jsx) | Recharts-based metrics visualization |
| [frontend/vite.config.js](file:///C:/Users/ishar/projects/amd/frontend/vite.config.js) | Vite proxy rules to backend |
| [ml/pipeline.py](file:///C:/Users/ishar/projects/amd/ml/pipeline.py) | Click CLI for ML pipeline (validate → preprocess → train → register) |
| [ml/stages/training.py](file:///C:/Users/ishar/projects/amd/ml/stages/training.py) | TF-IDF + LogisticRegression training with MLflow tracking |
| [scripts/build_router.py](file:///C:/Users/ishar/projects/amd/scripts/build_router.py) | Compiles fine-tuned adapter into Ollama as `llama3-router` |
| [scripts/generate_dataset.py](file:///C:/Users/ishar/projects/amd/scripts/generate_dataset.py) | Generates synthetic training CSV (2000 prompts, 4 categories) |
| [Modelfile](file:///C:/Users/ishar/projects/amd/Modelfile) | Ollama model definition for llama3-router (base: llama3.2:1b + QLoRA adapter) |
| [.env](file:///C:/Users/ishar/projects/amd/.env) | Environment config (ports, model names, tokens) |

**Current Progress:**
- ✅ Core FastAPI backend fully functional
- ✅ React/Vite dashboard fully functional
- ✅ 3-tier classification engine working (Tier 1 SLM now parses correctly)
- ✅ 84/84 unit tests passing (72.43% coverage)
- ✅ `llama3-router` compiled and registered in Ollama
- ✅ HuggingFace cloud fallback working with unified endpoint
- ✅ CI code quality (black) passing on GitHub
- ✅ ML pipeline Stages 1-2 passing
- ⬜ ML pipeline Stage 3 — fix applied (`multi_class` removed) but **not yet re-run**
- ⬜ Stress testing not yet performed
- ⬜ VRAM profiling not yet performed
- ⬜ `run.bat` startup script not yet created
- ⬜ Final screenshots/recordings not yet captured

---

## 4. Key Technical Decisions & Rationale

### Decision 1: HuggingFace Unified Endpoint
- **What:** Changed from `https://router.huggingface.co/hf-inference/v1/chat/completions` to `https://router.huggingface.co/v1/chat/completions`
- **Why:** The legacy endpoint is restricted; the unified endpoint auto-selects the best provider.
- **File:** [app/services/huggingface_client.py](file:///C:/Users/ishar/projects/amd/app/services/huggingface_client.py)

### Decision 2: Model Replacements
- **What:** Replaced `Phi-3` with `Qwen/Qwen2.5-7B-Instruct` and `Qwen/Qwen2.5-Coder-32B-Instruct`
- **Why:** Phi-3 was not available on HuggingFace Inference Providers; Qwen models are.

### Decision 3: Robust SLM JSON Parsing
- **What:** Added `re.search(r"\{.*\}", output_text, re.DOTALL)` before `json.loads()` in classifier.py
- **Why:** The `llama3-router` SLM wraps its JSON output with `assistant\n\n` prefix text that breaks `json.loads()`.

### Decision 4: Category Normalization
- **What:** Added category mapping logic: `"Programming"` → `"coding"`, `"Q&A"` → `"research"`, etc.
- **Why:** The fine-tuned SLM outputs inconsistent category names. Normalization ensures they map to valid routing rule keys.
- **What (also):** After normalization, models are fetched from `RoutingEngine.get_routing(category)` instead of using the SLM's hallucinated model names (e.g., `lstm`, `bert`).

### Decision 5: Vite Proxy Rewrite
- **What:** Added proxy rewrite in `vite.config.js` mapping `/api/metrics` → `/metrics/summary` on the backend.
- **Why:** Prometheus uses `/metrics` endpoint; frontend needed `/api/metrics/summary` to avoid clashing.

### Decision 6: Black Formatter Version Alignment
- **What:** Upgraded local black to `v26.5.1` to match GitHub Actions runner.
- **Why:** Minor formatting differences in SQL string wrapping between `v24.x` and `v26.x` caused CI `--check` failures.

---

## 5. Bugs Fixed During This Session

| # | Bug | Root Cause | Fix | File |
|:--|:---|:---|:---|:---|
| 1 | 403 auth error on HuggingFace | Wrong endpoint + token missing "Inference Providers" scope | Switched to unified endpoint; user provided correct token | `huggingface_client.py` |
| 2 | CI code quality failure (black) | Local black v24 vs CI black v26 formatting differences | Upgraded local black; reformatted all files | All `.py` files |
| 3 | Tier 1 SLM `json.loads()` failure | SLM output prefixed with `assistant\n\n` | Added regex JSON extraction before parsing | `classifier.py` |
| 4 | SLM returning invalid model names | SLM hallucinating model names like `lstm`, `bert` | Normalized category + fetch models from RoutingEngine config | `classifier.py` |
| 5 | `build_router.py` can't find adapter | Adapter files were in `Multi_Model_Router.../final_model/`, script looks in project root | Copied `adapter_model.safetensors` and `adapter_config.json` to project root | Manual copy |
| 6 | `ml.pipeline run` → `TypeError: unexpected keyword argument 'reg_C'` | Click option declared as `"reg_C"` but function parameter is `reg_c` | Changed click option to `"reg_c"` | `ml/pipeline.py` L75 |
| 7 | `LogisticRegression` → `TypeError: unexpected keyword argument 'multi_class'` | scikit-learn 1.7+ removed `multi_class` param | Removed `multi_class="multinomial"` from constructor | `ml/stages/training.py` L128 |
| 8 | `generate_dataset.py` UnicodeEncodeError on Windows | Python stdout defaults to cp1252 on Windows; can't encode `✓` | Set `PYTHONIOENCODING=utf-8` before running | Environment variable |

---

## 6. Environment & Configuration

### .env File (at `C:\Users\ishar\projects\amd\.env`)
```env
DEBUG=True
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_ROUTER_MODEL=llama3-router
OLLAMA_TIMEOUT=30
CHROMADB_DIR=./data/chromadb
DATABASE_URL=sqlite:///./data/metrics.db
HF_TOKEN=your_huggingface_token_here
# Model routing is configured in configs/routing_rules.yaml
MATH_PRIMARY_MODEL=huggingface:Qwen/Qwen2.5-72B-Instruct
# ... (additional model mappings in .env lines 32-43)
```

### Ollama Models Available Locally
| Model | Size | Purpose |
|:---|:---|:---|
| `llama3-router:latest` | 1.3 GB | **Fine-tuned router SLM** (Tier 1 classifier) |
| `llama3.2:1b` | 1.3 GB | Base model for llama3-router |
| `phi3:3.8b` | 2.2 GB | General purpose |
| `qwen2.5-coder:1.5b` | 986 MB | Code tasks |
| `qwen2.5-coder:3b` | 1.9 GB | Code tasks |
| `gemma2:2b` | 1.6 GB | General purpose |
| `qwen2.5:3b` | 1.9 GB | Default Ollama model |
| `gemma4:latest` | 9.6 GB | Large general purpose |
| `nomic-embed-text:latest` | 274 MB | ChromaDB embeddings |
| `mixtral:latest` | 26 GB | Large MoE model |
| `qwen3.6:latest` | 23 GB | Large general purpose |

### GPU Info (from Ollama startup logs)
```
NVIDIA GeForce RTX 5050 Laptop GPU
  CUDA 12.0, 8.0 GiB total, ~6.9 GiB available
  Driver: 13.3
Intel UHD Graphics 770 (integrated, disabled for Ollama)
```

---

## 7. Team Task Delegation

A detailed task checklist was created at [teammate_tasks.md](file:///C:/Users/ishar/.gemini/antigravity-cli/brain/a4abe363-92c0-4df4-84e5-bc0054b016cb/teammate_tasks.md).

**Role assignments:**
| Role | Assignee | Focus |
|:---|:---|:---|
| 💻 Frontend Developer | Teammate | Dashboard validation, screenshots, walkthrough recording |
| 🗄️ Database, Testing & Stress Testing | **User (Ishar)** | DB init, prompt seeding, stress testing, transaction logging |
| 🧠 Model & ML Engineer | **User (Ishar)** | SLM compilation, inference validation, VRAM profiling, MLflow pipeline |
| ⚙️ DevOps & Integration | Teammate | `run.bat` script, fallback simulation, final QA, CI cleanup |

**Timeline:** All tasks compressed into a single day (July 10, 2026):
- 11:30 AM - 1:30 PM: Sprint 1 (Setup & Compilation) — **DONE**
- 2:30 PM - 4:30 PM: Sprint 2 (Data Seeding & Integration)
- 5:00 PM - 7:00 PM: Sprint 3 (Stress Testing & MLOps)
- 7:00 PM - 9:00 PM: Sprint 4 (Cleanup & Deliverables)

---

## 8. Outstanding Tasks (Immediate)

### 🔴 Must Do Next (in order)
1. **Re-run ML pipeline** — The `multi_class` fix was applied but the pipeline has not been re-executed yet.
   ```powershell
   $env:PYTHONIOENCODING="utf-8" ; .venv\Scripts\python -m ml.pipeline run --data-path ./data/training_dataset.csv --version 1.0.0 --auto-promote
   ```
2. **Restart all services** — Ollama, backend, and frontend were killed by a server restart and need to be relaunched:
   ```powershell
   # Terminal 1:
   ollama serve
   # Terminal 2:
   .venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   # Terminal 3:
   cd frontend && npm run dev
   ```
3. **Commit all recent fixes** — The following files were modified but NOT yet committed/pushed:
   - `app/services/classifier.py` — Robust JSON extraction + category normalization + RoutingEngine model lookup
   - `ml/pipeline.py` — `reg_C` → `reg_c` fix
   - `ml/stages/training.py` — Removed `multi_class="multinomial"`
   - Root directory now has copies of `adapter_model.safetensors` and `adapter_config.json`

### 🟡 Medium-Term (Today)
4. **Database stress test** — Run 100+ parallel queries to verify SQLite write-lock handling.
5. **VRAM profiling** — Monitor GPU memory during rapid model swaps using Ollama.
6. **Seed custom prompts** — Use `/classify/seed` POST endpoint to add evaluation prompts.
7. **Validate `/metrics/summary`** — Ensure all dashboard fields populate correctly.
8. **Create `run.bat`** — Single-click startup for Windows (launches backend + frontend).
9. **Simulate fallback failover** — Invalidate HF token temporarily, verify graceful degradation.
10. **Add `black[jupyter]` to `requirements-dev.txt`** — Eliminates CI Jupyter warning.

### 🟢 Final (Tonight)
11. **Run full `pytest` suite** — Verify all 84 tests still pass after changes.
12. **Capture screenshots/recordings** — Save to `assets/` folder.
13. **Final merge** — Merge `testing` → `main`, push to GitHub.

---

## 9. Commands Quick Reference

```powershell
# Start all services
ollama serve
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev

# Health check
curl http://localhost:8000/health

# Run ML pipeline
$env:PYTHONIOENCODING="utf-8" ; .venv\Scripts\python -m ml.pipeline run --data-path ./data/training_dataset.csv --version 1.0.0 --auto-promote

# Generate training dataset
$env:PYTHONIOENCODING="utf-8" ; .venv\Scripts\python scripts/generate_dataset.py

# Build router model
.venv\Scripts\python scripts/build_router.py

# Run tests
.venv\Scripts\pytest -v

# Format code
.venv\Scripts\black .

# Git workflow
git add -A && git commit -m "message" && git push origin testing
git checkout main && git merge testing && git push origin main
```

---

## 10. Knowledge Transfer Package (Paste Into New Chat)

```
PROJECT: AMD Multi-Model Fallback Router (Hackathon, Day 4-5)
WORKSPACE: C:\Users\ishar\projects\amd
REPO: isharpals-06/AMD_Hackathon (branches: main, testing)
CURRENT BRANCH: testing

STACK: FastAPI backend (port 8000) + React/Vite frontend (port 5173) + Ollama (port 11434) + SQLite + ChromaDB + MLflow

3-TIER CLASSIFIER: llama3-router SLM (Tier 1) → ChromaDB (Tier 2) → Regex (Tier 3)
CATEGORIES: math, coding, research, casual_chat
ROUTING CONFIG: configs/routing_rules.yaml maps categories to primary/fallback models

CRITICAL CONTEXT:
- HF_TOKEN: Configured locally in .env (requires Inference Providers scope)
- HF endpoint: https://router.huggingface.co/v1/chat/completions (unified, NOT /hf-inference/)
- GPU: NVIDIA RTX 5050 (8GB VRAM, CUDA 12.0)
- Python: 3.11 via uv
- Ollama: v0.30.10, has llama3-router:latest compiled
- Windows quirk: use $env:PYTHONIOENCODING="utf-8" before running scripts with Unicode chars

RECENT FIXES (applied but NOT yet committed):
1. classifier.py — regex JSON extraction from SLM output + category normalization + RoutingEngine model lookup
2. ml/pipeline.py L75 — "reg_C" → "reg_c" (click option casing mismatch)
3. ml/stages/training.py L128 — removed multi_class="multinomial" (scikit-learn 1.7+ compat)
4. adapter_model.safetensors + adapter_config.json copied to project root (build_router.py needs them there)

WHAT WORKS: Backend, frontend, 3-tier classification, HF cloud fallback, 84/84 tests, CI black formatting, dataset generation, ML pipeline stages 1-2
WHAT'S LEFT: Re-run ML pipeline stage 3+4, stress test DB, VRAM profiling, create run.bat, capture screenshots, final commit+merge

TEAM: 4 people. User handles Model/ML + Database/Testing. Two teammates handle Frontend and DevOps.
DEADLINE: Everything must be done today (July 10, 2026).
```
