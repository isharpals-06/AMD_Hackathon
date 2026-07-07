# 📋 Product Requirements Document (PRD)
**Project:** Intelligent Multi-Model Fallback Router  
**Target Architecture:** FastAPI Backend (AMD ROCm GPU) + React & Vite Frontend Dashboard  

---

## 1. Executive Summary & Goal
The objective is to build an intelligent, cost-optimized, and hardware-stable multi-model routing system. 

When a user submits a prompt, the router dynamically selects the most appropriate model based on task complexity (e.g. coding vs. general chat) and routes the request. If the primary model fails or exceeds latency/VRAM safety boundaries, the system seamlessly redirects the request to a fallback model.

---

## 2. Key Architecture Pillars
1.  **FastAPI Backend Server:** Services requests, tracks latency/token telemetry, and manages database logs.
2.  **3-Tier Hybrid Classification Engine:**
    *   *Tier 1 (Cognitive SLM):* Queries a local fine-tuned `Llama-3.2-1B` model to categorize the task and select the optimal model.
    *   *Tier 2 (Vector Database Fallback):* If the SLM fails, it uses ChromaDB vector search (with `nomic-embed-text` embeddings) against seed examples.
    *   *Tier 3 (Regex Fallback):* Key phrase patterns act as the final safe fallback.
3.  **Local ROCm Model Suite:** Run all model inference locally on AMD GPU hardware.
4.  **React + Vite Frontend Dashboard:** Provides user-friendly prompt testing and displays real-time performance and cost savings telemetry.

---

## 3. Approved Model Suite
To optimize task performance while respecting hardware memory boundaries, the following models are configured:

| Task Type | Primary Model | Fallback Model | Purpose |
| :--- | :--- | :--- | :--- |
| **Coding** | `kimi-k2p7-code` | `gemma-4-31b-it` | Specialized programming reasoning |
| **Math** | `gemma-4-31b-it` | `gemma-4-31b-it-nvfp4` | High-complexity math and logic |
| **Research** | `gemma-4-26b-a4b-it` | `gemma-4-31b-it` | Detailed summarization & data extraction |
| **Casual Chat** | `minimax-m3` | `gemma-4-26b-a4b-it` | Fast greeting/conversational queries |

---

## 4. User Experience & Dashboard Requirements
The React + Vite frontend must support:
*   **Playground Panel:** Input box for prompt testing, routing execution indicators, and raw model output display.
*   **Metrics Telemetry Grid:** Shows execution time, model used, fallback status, tokens generated, and tokens/sec.
*   **Analytics Graphs:** Visualizes cumulative cost savings relative to a single-model baseline and VRAM utilization.
