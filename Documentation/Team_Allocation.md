# 👥 Team Task Allocation (4-Person Restructure)
**Project:** Intelligent Multi-Model Fallback Router  

---

## 👥 Restructured Roles & Deliverables

### 👤 Person 1: Lead Architect, Ollama & Model Systems (You)
*   **Focus:** Ollama server configs, local model loading pipelines, tokenizer setups, and VRAM management.  
*   **Tasks:**
    *   Configure local Ollama and compile the fine-tuned `llama3-router` using the Modelfile.
    *   Set up CPU/GPU model swap wrappers and cache-clearing mechanisms (`keep_alive: 0` offloading).
    *   Implement loading and tokenization pipelines for the 5 target models on local ROCm GPU.
    *   Execute the HF weight warming and caching script (`cache_models.py`) on the AMD Cloud instance.
*   **Day 5 Deliverable:** Robust local model loading and swapping pipeline with optimized VRAM offloading.

---

### 👤 Person 2: Task Classifier (Classification Engine)
*   **Focus:** Categorization accuracy across prompt types.  
*   **Tasks:**
    *   Set up the loading wrapper for the fine-tuned `llama-router` QLoRA model.
    *   Implement ChromaDB vector search fallback using `nomic-embed-text` embeddings.
    *   Construct regex keyword parsing checks as a final safety fallback.
*   **Day 5 Deliverable:** 3-tier hybrid task classifier (SLM -> ChromaDB -> Regex) running with <150ms classification latency.

---

### 👤 Person 3: SQLite Database & Telemetry Metrics
*   **Focus:** Persistent backend logging, token analytics, and cost metrics.  
*   **Tasks:**
    *   Configure the SQLite database schema to log active models, swaps, and latencies.
    *   Write SQL aggregate queries to service the `/metrics` dashboard backend.
    *   Build virtual cost calculators and comparison logic relative to baseline.
*   **Day 5 Deliverable:** Persistent database backend delivering real-time aggregated latency and cost reports.

---

### 👤 Person 4: React Frontend, Dashboard Analytics & QA
*   **Focus:** User interface and performance testing.  
*   **Tasks:**
    *   Create the React + Vite dashboard app.
    *   Implement graphs and panels summarizing tokens, latency, cost savings, and active models.
    *   Connect UI components to backend endpoints (`/process`, `/metrics`, `/health`).
    *   Lead the execution of the 10 verification test cases.
*   **Day 5 Deliverable:** Interactive frontend dashboard and final recorded demo showcasing model swapping.
