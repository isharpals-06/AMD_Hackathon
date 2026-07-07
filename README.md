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
├── notebook_code.py            # Clean Python implementation of router cells for notebook
├── Documentation/              # System architecture, setup guides, and test cases
│   ├── PRD_MultiModelRouter.md
│   ├── TDD_MultiModelRouter.md
│   ├── Developer_Setup_Guide.md
│   ├── Test_Plan_and_Cases.md
│   └── Updated_Hackathon_Plan.md
├── scripts/
│   ├── init_db.py              # SQLite database table initializer
│   ├── merge_lora.py           # LoRA weight merging script (optional)
│   └── generate_dataset.py     # Generates synthetic local datasets (2000 rows CSV)
├── requirements.txt            # Python environment dependencies
├── Modelfile                   # Ollama local model build template for QLoRA
└── .gitignore                  # Git tracking ignore rules
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

### 4. Run the Jupyter Notebook Server
Launch JupyterLab on your AMD Cloud instance to run the model router:
```bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
```

### 5. Open the Router Notebook
1. Open the notebook `Multi_Model_Router_AMD_Cloud.ipynb` in your browser.
2. Reference or copy the clean Python cells from [notebook_code.py](file:///mnt/c/Users/ishar/Projects/AMD/app/notebook_code.py) to implement the core VRAM Manager and Routing Engine.
3. Run the cells to interact with the widgets interface.

---

## 👥 Team Roles (4-Person Restructure)

*   **Person 1: Lead Architect & GPU VRAM Systems (User)** - Configures PyTorch memory hooks on ROCm, manages the dynamic model loader/unloader (`empty_cache`/`gc`), and maintains the SQLite logging backend.
*   **Person 2: Task Classifier & NLP Engine** - Sets up the in-memory ChromaDB instance in the notebook, integrates local embedding encoders, and manages regex fallback rules.
*   **Person 3: Model Integrations & ROCm Tuning** - Integrates HuggingFace model weight pipelines, tunes parameters (quantization/precision) for local target models (`minimax-m3`, `kimi-k2p7-code`, `gemma-4` series), and tracks tokens.
*   **Person 4: Notebook UI, Analytics Dashboard & QA** - Builds the interactive widgets console, compiles metric summaries, executes the test suite, and conducts benchmarking checks for final submission.
