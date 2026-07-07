# 👥 Team Task Allocation (4-Person Restructure)
**Project:** Intelligent Multi-Model Fallback Router  

---

## 👥 Restructured Roles & Deliverables

### 👤 Person 1: Lead Architect & GPU VRAM Systems (You)
*   **Focus:** Core server integration, VRAM memory lifecycle manager, and logging schema.  
*   **Tasks:**
    *   Build backend wrapper functions to handle local VRAM tracking.
    *   Initialize the SQLite database schema to store token and latency telemetry.
    *   Lead server configuration and ROCm execution environment setup.
*   **Day 5 Deliverable:** End-to-end routing backend with zero memory leakage under sequential stress.

---

### 👤 Person 2: Task Classifier (Classification Engine)
*   **Focus:** Categorization accuracy across prompt types.  
*   **Tasks:**
    *   Set up the loading wrapper for the fine-tuned `llama-router` QLoRA model.
    *   Implement ChromaDB vector search fallback using `nomic-embed-text` embeddings.
    *   Construct regex keyword parsing checks as a final safety fallback.
*   **Day 5 Deliverable:** 3-tier hybrid task classifier (SLM -> ChromaDB -> Regex) running with <150ms classification latency.

---

### 👤 Person 3: Model Integrations & ROCm Tuning
*   **Focus:** Model weight downloads, quantization parameters, and generation execution.  
*   **Tasks:**
    *   Write HuggingFace model loading and tokenization routines.
    *   Apply `BitsAndBytesConfig` 4-bit precision to fit the larger 31B models in GPU memory.
    *   Build token counters to record inputs/outputs tokens.
*   **Day 5 Deliverable:** Cached local weights running successfully on ROCm with optimized precision.

---

### 👤 Person 4: React Frontend, Dashboard Analytics & QA
*   **Focus:** User interface and performance testing.  
*   **Tasks:**
    *   Create the React + Vite dashboard app.
    *   Implement graphs and panels summarizing tokens, latency, cost savings, and active models.
    *   Connect UI components to backend endpoints (`/process`, `/metrics`, `/health`).
    *   Lead the execution of the 10 verification test cases.
*   **Day 5 Deliverable:** Interactive frontend dashboard and final recorded demo showcasing model swapping.
