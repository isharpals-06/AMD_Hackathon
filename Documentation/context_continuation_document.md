# AMD Developer Hackathon: Conversation Continuation Document

This document captures all the contexts, architectural decisions, and current states of the Multi-Model Router project to ensure a seamless transition to a new session context.

---

## 1. Executive Summary
*   **Main Goals:** Build a production-grade Multi-Model Fallback Router for the AMD Developer Hackathon. The router must classify incoming user prompts into four task categories (Math, Coding, Research, Casual) and route them to optimal primary models, with automated fallback logic to secondary models in case of VRAM exhaustion or service timeout events.
*   **Current Status:** All backend FastAPI endpoints (`/process`, `/metrics`, `/config`, `/health`), SQLite schema logs, and custom dark-theme frontend dashboards are fully integrated, tested, and running natively on Windows.
*   **Most Important Conclusions:** 
    1.  *Hardware Constraints:* Teammates with older, GPU-less laptops can run the entire project by routing execution to free Hugging Face serverless cloud models.
    2.  *Ollama Path Mappings:* On Windows, Ollama background services require absolute backslash paths (`C:\...\`) in the `Modelfile` to successfully locate LoRA companion files (like `adapter_config.json`).
    3.  *OfflineSnappiness:* Bypassing local models on startup using a health check prevents UI freezes when Ollama is offline.

---

## 2. User Profile & Preferences
*   **Interests:** Machine learning engineering, edge deployments, and efficient model orchestration.
*   **Skill Level:** Advanced developer utilizing WSL (Kali Linux) and native Windows PowerShell environments.
*   **Learning Preferences:** Clear documentation, copy-pasteable script commands, and deep conceptual explanations of pathing and networking behaviors.
*   **Constraints:** Local GPU (RTX 5050 Laptop) has low VRAM (8GB), and teammates do not have WSL or dedicated GPUs. 
*   **Long-Term Goals:** Deliver a winning Hackathon submission showing cost savings, latency metrics, and robust model swapping mechanics on AMD architectures.

---

## 3. Projects & Ideas Discussed

### Project: Multi-Model Fallback Router
*   **Purpose:** Dynamically balance prompt routing based on difficulty. Simple prompts (Casual Chat) go to small 1.5B/3B models, while complex prompts (Coding/Math) route to 32B/72B models, saving costs and VRAM.
*   **Current Progress:** 100% of today's integration tasks are complete. Running natively on Windows.
*   **Key Design Decisions:**
    *   *3-Tier Classification:* Staged checks (Tier 1: local `llama3-router` SLM $\rightarrow$ Tier 2: ChromaDB embeddings $\rightarrow$ Tier 3: Local regex rules).
    *   *VRAM Swapping:* Unloading active models immediately (`keep_alive: 0`) prevents GPU memory overflow.
    *   *Consolidated Runner:* Spawning both servers simultaneously using a single batch runner (`run.bat`).
*   **Open Questions:** None at this stage. All connection problems are resolved.
*   **Next Steps:** Distribute tasks to teammates for data seeding (ChromaDB prompts), stress testing, and demo recording.

---

## 4. Research Topics Covered
*   **Client-Server File Resolution:** Explored how the Ollama daemon handles relative path compilation relative to the service installation folder rather than the host shell directory.
*   **Go Filepath Separator Parsing:** Analyzed how Go’s `filepath.Dir` library on Windows fails to recognize Unix forward slashes (`/`), interpreting paths as single filenames and returning `.` as the directory.
*   **Vite Proxy Routing:** Configured Vite’s reverse proxy to route `/api/*` to FastAPI port `8000` to prevent CORS issues.

---

## 5. Plans & Roadmaps Created
*   **Day 3 Milestone (Integration):** Checked teammate submissions, merged branches, resolved CSS overlaps, configured Vite reverse proxies, and added a dynamic config retrieval system.
*   **Day 4 Milestone (Evaluation):** Stress test the router, gather data on cost savings, compile local checkpoints, and record screen recordings.
*   **Day 5 Milestone (Submission):** Slide deck assembly, repository cleanup, and final upload.

---

## 6. Important Recommendations Given
*   **Technical:** Always use absolute Windows backslash paths (`C:\...\`) when defining `ADAPTER` directions in Ollama Modelfiles on Windows.
*   **Strategic:** Allow teammates to test the application by configuring `.env` to route prompts to HuggingFace Serverless APIs. This bypasses local hardware constraints completely.

---

## 7. Decisions Already Made
*   **No Simulation Mode:** Real execution is mandatory. Handled by creating keyless HuggingFace completions proxies.
*   **Folder Restructure:** Renamed `Multi_Model_Router_Llama3_QLoRA_Finetuning.ipynb` directory to `notebooks` and moved screenshot directories into `assets/` to declutter the root.

---

## 8. Context Needed for Future Conversations
*   **Sandbox Isolation:** The AI sandbox runs offline, causing HuggingFace APIs to return `No address associated with hostname` during tests. This is normal and works fine on the user's internet-connected machine.
*   **Database Schema:** The SQLite table is named `requests` and resides in `data/metrics.db`.

---

## 9. Outstanding Tasks
*   **Immediate:** Run `python scripts/build_router.py` to compile the router model (works cross-platform on Windows and Linux/WSL).
*   **Medium-Term:** Let teammates add ChromaDB seed examples inside `app/services/classifier.py`.
*   **Long-Term:** Capture cost savings statistics from the `/metrics` page for the final slides.

---

## 10. Knowledge Transfer Package (Copy-Paste)
```text
================================================================================
AMD DEVELOPER HACKATHON CONTEXT: MULTI-MODEL ROUTER
================================================================================
- OS: Windows 11 (PowerShell terminal).
- App Root: C:\Users\ishar\projects\amd
- Backend: FastAPI (Port 8000), database logged to data/metrics.db.
- Frontend: Vite React SPA (Port 5173), proxy mapped via /api.
- Classifier: 3-Tier Staged (SLM -> ChromaDB -> Regex).
- Active Models (.env / config.py):
  - Math: huggingface:Qwen/Qwen2.5-Math-7B-Instruct (Fallback: Llama-3.1-8B)
  - Coding: huggingface:Qwen/Qwen2.5-Coder-32B-Instruct (Fallback: Coder-7B)
  - Research: huggingface:meta-llama/Llama-3.1-8B-Instruct (Fallback: Phi-3-mini)
  - Casual: huggingface:microsoft/Phi-3-mini-4k-instruct (Fallback: Qwen2.5-7B)
- Ollama Router: compiled using:
  ADAPTER "C:\Users\ishar\projects\amd\adapter_model.safetensors"
- Unified Launch Script: double-click run.bat in the root folder.
================================================================================
```
