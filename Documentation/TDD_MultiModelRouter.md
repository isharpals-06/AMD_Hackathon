# Technical Design Document (TDD)
## Multi-Model Fallback Router

**Project:** Multi-Model Fallback Router  
**Version:** 1.0  
**Date:** July 2026  
**Author:** Team  

---

## 1. System Architecture Overview

### High-Level Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                     USER LAYER                                   │
│                                                                   │
│  CLI Interface (Click/Typer)  |  Optional: Web UI (React)      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                   APPLICATION LAYER (FastAPI)                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Request Handler                                         │   │
│  │ - Validate input                                        │   │
│  │ - Log incoming request                                  │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Task Classifier                                         │   │
│  │ - Vector-based semantic search (ChromaDB)                │   │
│  │ - Fallback: Regex classification                        │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
│  ┌──────────────────▼──────────────────────────────────────┐   │
│  │ Router Decision Engine                                  │   │
│  │ - Select primary & fallback models                      │   │
│  │ - Load routing rules from config                        │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
│  ┌──────────────────▼──────────────────────────────────────┐   │
│  │ Executor                                                │   │
│  │ - Call primary model                                    │   │
│  │ - On failure: call fallback                             │   │
│  │ - Handle timeouts, rate limits, errors                 │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
└─────────────────────┼────────────────────────────────────────────┘
                      │
       ┌──────────────┴──────────────┐
       │                             │
┌──────▼────────────┐      ┌────────▼──────────┐
│  INTEGRATION      │      │  LOGGING LAYER    │
│  LAYER            │      │                   │
├──────────────────┤      ├──────────────────┤
│                  │      │                  │
│ • Ollama Client  │      │ • Request Log    │
│   (local HTTP)   │      │ • Response Log   │
│                  │      │ • Metrics DB     │
│ • Fireworks      │      │ • Error Log      │
│   API Client     │      │                  │
│                  │      │                  │
│ • Token Counter  │      │                  │
│ • Error Handler  │      │                  │
│                  │      │                  │
└──────┬───────────┘      └────────┬─────────┘
       │                            │
       ▼                            ▼
┌──────────────────────────────────────────┐
│      EXTERNAL SERVICES                    │
│                                           │
│ • Ollama (Local)                          │
│   - Qwen 7B model                         │
│   - Runs on local machine/AMD GPU         │
│                                           │
│ • Fireworks API (Cloud)                   │
│   - Mixtral 8x7B                          │
│   - Qwen-72B                              │
│   - Runs on AMD ROCm infrastructure       │
│                                           │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│      DATA PERSISTENCE                     │
│                                           │
│ • SQLite Database                         │
│   - Request logs                          │
│   - Metrics (tokens, latency, cost)       │
│                                           │
│ • ChromaDB (Vector DB)                    │
│   - Seed examples for classification     │
└──────────────────────────────────────────┘
```

---

## 2. Component Breakdown & Interactions

### 2.1 Core Components

#### A. Request Handler
**Responsibility:** Entry point, input validation, request logging
```
Input:
  {
    "prompt": string (required),
    "task_type": string (optional, auto-detected if not provided)
  }

Process:
  1. Validate prompt length (min: 10 chars, max: 50,000 chars)
  2. Validate task_type (if provided)
  3. Generate request_id (UUID)
  4. Log request to database
  5. Pass to Task Classifier

Output:
  request_id: string (UUID)
  status: "received" | "processing" | "completed" | "failed"
```

#### B. Task Classifier
**Responsibility:** Classify incoming prompts by semantic similarity using a local vector database, with keyword regex as a fallback.

```python
# Semantic search logic:
# 1. Input prompt is embedded using 'nomic-embed-text' via Ollama.
# 2. ChromaDB queries top 3 nearest neighbor examples.
# 3. Categorize task based on majority class of nearest neighbors.
# 4. If ChromaDB or Ollama embedding fails:
#    Fall back to keyword-based regex classification.

Regex Rules (Fallback):
  if "summarize" in prompt.lower() OR "summary" in prompt:
      task_type = "summarization"
  elif "review" in prompt.lower() AND ("code" in prompt OR "function" in prompt):
      task_type = "code_review"
  elif "code" in prompt.lower() OR "write" in prompt OR "implement" in prompt:
      task_type = "coding"
  else:
      task_type = "general" (fallback to Mixtral)

Accuracy Target:
  - 90%+ accurate classification on test suite
  - Edge cases logged for manual review
```

#### C. Router Decision Engine
**Responsibility:** Select primary & fallback models based on task type
```
Routing Rules:
  task_type: "summarization"
    primary: "ollama:qwen"
    fallback: "fireworks:mixtral"
    timeout: 10 seconds
    max_retries: 1

  task_type: "coding"
    primary: "fireworks:mixtral"
    fallback: "fireworks:qwen-72b"
    timeout: 15 seconds
    max_retries: 1

  task_type: "code_review"
    primary: "fireworks:mixtral"
    fallback: "fireworks:qwen-72b"
    timeout: 15 seconds
    max_retries: 1

  task_type: "general"
    primary: "fireworks:mixtral"
    fallback: "fireworks:qwen-72b"
    timeout: 15 seconds
    max_retries: 1

Output:
  {
    "primary_model": string,
    "fallback_model": string,
    "timeout_seconds": int,
    "max_retries": int
  }
```

#### D. Executor
**Responsibility:** Call models, handle failures, manage retries
```
Flow:
  1. Call primary model API
  2. Handle response:
     - On success: Parse, extract tokens, return result
     - On timeout: Retry with fallback
     - On rate limit (429): Log, retry with fallback
     - On error (5xx): Log, retry with fallback
     - On parse error: Log error, don't retry (bad request)
  3. Call fallback model if primary fails
  4. If fallback also fails: Return error to user
  5. Track all attempts in metrics

Error Handling:
  - Timeout → Automatic retry with fallback
  - 429 (Rate Limit) → Automatic retry with fallback
  - 500+ (Server Error) → Automatic retry with fallback
  - 400-level (Client Error) → Don't retry, return error
  - Connection Error → Retry up to max_retries
```

#### E. Token Counter & Cost Calculator
**Responsibility:** Track tokens and calculate costs
```
For Ollama Requests:
  - Estimate tokens using simple character count heuristic
  - Formula: tokens ≈ char_count / 4
  - Ollama is free locally, so cost = $0

For Fireworks Requests:
  - Extract token count from API response
  - Response format:
    {
      "usage": {
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int
      }
    }
  - Calculate cost based on Fireworks pricing
    - Mixtral: $0.0005 per 1k input tokens, $0.0015 per 1k output tokens
    - Qwen-72B: $0.0003 per 1k input tokens, $0.001 per 1k output tokens

Output:
  {
    "total_tokens": int,
    "input_tokens": int,
    "output_tokens": int,
    "cost_usd": float,
    "model": string
  }
```

#### F. Metrics & Logging System
**Responsibility:** Track all requests and metrics
```
Database Schema:
  requests table:
    - request_id (PK)
    - timestamp
    - prompt
    - task_type (classified)
    - primary_model
    - fallback_model_used (boolean)
    - final_model_used
    - status (success | timeout | error | retry)
    - response
    - tokens_used
    - cost_usd
    - latency_ms
    - error_message (if failed)

Metrics Calculated:
  - Total requests
  - Success rate
  - Average latency per model
  - Total tokens by model
  - Total cost by model
  - Fallback frequency
  - Error distribution
```

---

## 3. Technology Stack & Rationale

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend Framework** | FastAPI | Fast, async, built-in validation, easy to test |
| **Language** | Python 3.10+ | Rich ML ecosystem, fast development |
| **Async Runtime** | asyncio + uvicorn | Handle concurrent requests efficiently |
| **HTTP Client** | httpx | Async HTTP client, better than requests for FastAPI |
| **Metrics DB** | SQLite | Zero-config, lightweight, sufficient for structured logging & metrics |
| **Vector DB** | ChromaDB | In-memory, local vector search for semantic classification |
| **Local Models** | Ollama + Qwen 7B | Easy setup, open-source, AMD-friendly |
| **Cloud API** | Fireworks AI | AMD-powered, cost-efficient, good API |
| **CLI** | Click or Typer | Simple, user-friendly CLI tool |
| **Web (Optional)** | React + Vite | Fast setup, minimal dependencies |
| **Containerization** | Docker + Docker Compose | Easy deployment, reproducible |
| **Testing** | pytest | Standard Python testing framework |
| **Logging** | Python logging + SQLite | Built-in, persistent |

---

## 4. Data Flow Diagrams

### 4.1 Happy Path (Summarization Task)
```
User Input:
  {
    "prompt": "Summarize this 2000-word article: [article text]",
    "task_type": "summarization"
  }
        │
        ▼
Request Handler:
  - Validate input ✓
  - Generate request_id: "req-12345"
  - Log to database
        │
        ▼
Task Classifier:
  - Detect: "summarization"
  - Confidence: 95%
        │
        ▼
Router Decision Engine:
  - Task: summarization
  - Primary: ollama:qwen
  - Fallback: fireworks:mixtral
  - Timeout: 10s
        │
        ▼
Executor:
  - Call Ollama HTTP endpoint
  - Ollama responds in 2.3 seconds
  - Response: "The article discusses..."
  - Status: SUCCESS
        │
        ▼
Token Counter:
  - Count tokens in prompt: ~500
  - Count tokens in response: ~187
  - Total: 687 tokens
  - Cost: $0 (local model)
        │
        ▼
Metrics Logger:
  - Save to database
  - request_id: "req-12345"
  - model_used: "ollama:qwen"
  - tokens: 687
  - latency_ms: 2300
  - status: "success"
        │
        ▼
Return to User:
  {
    "result": "The article discusses...",
    "tokens_used": 687,
    "model_used": "ollama:qwen",
    "latency_ms": 2300,
    "cost_usd": 0.0,
    "status": "success"
  }
```

### 4.2 Fallback Path (Timeout Scenario)
```
User Input:
  {
    "prompt": "Generate a complex sorting algorithm in Rust",
    "task_type": "coding"
  }
        │
        ▼
Request Handler: ✓ Validate & log
        │
        ▼
Task Classifier: ✓ Detect "coding"
        │
        ▼
Router Decision Engine:
  - Primary: fireworks:mixtral
  - Fallback: fireworks:qwen-72b
  - Timeout: 15s
        │
        ▼
Executor - Attempt 1:
  - Call Fireworks Mixtral
  - Wait 15 seconds...
  - TIMEOUT ❌
  - Log timeout event
  - Set: fallback_used = true
        │
        ▼
Executor - Attempt 2 (Fallback):
  - Call Fireworks Qwen-72B
  - Qwen responds in 8 seconds ✓
  - Response: "fn sort_array(arr: &mut Vec<i32>) { ... }"
  - Status: SUCCESS (via fallback)
        │
        ▼
Token Counter:
  - Qwen-72B response: 950 tokens
  - Cost: $0.0003 per 1k input + $0.001 per 1k output
  - Total cost: ~$0.001
        │
        ▼
Metrics Logger:
  - primary_model: "fireworks:mixtral"
  - fallback_model_used: true
  - final_model_used: "fireworks:qwen-72b"
  - status: "success_via_fallback"
  - tokens: 950
  - cost: $0.001
        │
        ▼
Return to User:
  {
    "result": "fn sort_array(arr: &mut Vec<i32>) { ... }",
    "tokens_used": 950,
    "model_used": "fireworks:qwen-72b (fallback)",
    "latency_ms": 8000,
    "cost_usd": 0.001,
    "status": "success_via_fallback"
  }
```

### 4.3 Error Path (Both Models Fail)
```
User Input: [valid request]
        │
        ▼
Request Handler: ✓
        │
        ▼
Task Classifier: ✓
        │
        ▼
Router Decision Engine: ✓
        │
        ▼
Executor - Attempt 1:
  - Call Fireworks Mixtral
  - Error: 429 (rate limit) ❌
  - Log error, prepare fallback
        │
        ▼
Executor - Attempt 2:
  - Call Fireworks Qwen-72B
  - Error: 500 (server error) ❌
  - Both models failed
  - Max retries exceeded
        │
        ▼
Error Handler:
  - Create error response
  - Log failure to database
  - Return error to user
        │
        ▼
Return to User:
  {
    "error": "All models failed",
    "detail": "Primary model (Mixtral) returned 429. Fallback (Qwen-72B) returned 500.",
    "status": "failed",
    "request_id": "req-12345"
  }
```

---

## 5. Security Architecture

### 5.1 Input Validation
- Prompt length: min 10 chars, max 50,000 chars
- Task type: must be one of ["summarization", "coding", "code_review", "general"]
- No SQL injection possible (using parameterized queries in SQLite)
- No prompt injection mitigation needed (we're not system-aware)

### 5.2 API Key Management
- Fireworks API key stored in environment variables
- NOT in code or version control
- Docker Compose uses `.env` file (excluded from git)
- Clear setup documentation on how to provide API key

### 5.3 Rate Limiting
- Implement per-IP rate limiting (optional, if needed)
- Monitor Fireworks API quota
- Log rate limit errors and fallback usage
- Alert if quota running low

### 5.4 Data Privacy
- Prompts are logged locally (SQLite)
- No data sent to external parties except Fireworks API
- Ollama runs locally, no data leaves machine
- Users can clear database if concerned about privacy

---

## 6. Performance & Scalability Considerations

### 6.1 Latency Targets
| Component | Target | Notes |
|-----------|--------|-------|
| Request validation | <50ms | Local processing |
| Task classification | <50ms | Regex matching |
| Router decision | <10ms | Lookup in config |
| Ollama inference | 2-5s | Local, depends on hardware |
| Fireworks API call | 5-15s | Network + inference |
| Token counting | <100ms | String processing |
| Database logging | <100ms | Async write |
| **Total (Ollama)** | **3-6s** | Summarization path |
| **Total (Fireworks)** | **6-18s** | Coding/review path |

### 6.2 Throughput
- Single instance: ~10 concurrent requests (limited by Fireworks API rate limits)
- Fireworks API provides ~100 requests/minute on free tier
- Ollama: Limited by local hardware (GPU/CPU)

### 6.3 Resource Usage
| Resource | Local Dev | Docker Container |
|----------|-----------|-----------------|
| CPU | 2+ cores | 4 cores recommended |
| RAM | 4GB+ | 8GB if running Ollama locally |
| Disk | 5GB (Ollama models) | Same |
| Network | Fireworks API calls | Same |

### 6.4 Caching Strategy
- No caching implemented for MVP (tokens would be identical)
- Could add request deduplication in future
- Cache model responses if same prompt requested twice

### 6.5 Optimization Opportunities
1. **Batch requests:** Process multiple requests together (not for hackathon)
2. **Model caching:** Keep models warm in memory
3. **Connection pooling:** Reuse HTTP connections to APIs
4. **Async processing:** Use task queues for long-running requests

---

## 7. Database Schema

### SQLite Tables

#### requests
```sql
CREATE TABLE requests (
  request_id TEXT PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  prompt TEXT NOT NULL,
  task_type TEXT,  -- "summarization", "coding", "code_review", "general"
  prompt_length INT,
  primary_model TEXT,
  fallback_model_used BOOLEAN DEFAULT FALSE,
  final_model_used TEXT,
  status TEXT,  -- "success", "timeout", "error", "success_via_fallback"
  response TEXT,
  response_length INT,
  tokens_used INT,
  input_tokens INT,
  output_tokens INT,
  cost_usd FLOAT,
  latency_ms INT,
  error_message TEXT
);

CREATE INDEX idx_task_type ON requests(task_type);
CREATE INDEX idx_created_at ON requests(created_at);
CREATE INDEX idx_status ON requests(status);
```

#### metrics
```sql
CREATE TABLE metrics (
  metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  metric_name TEXT,  -- "total_tokens", "success_rate", "avg_latency"
  metric_value FLOAT,
  model TEXT,
  task_type TEXT,
  period TEXT  -- "1h", "1d", "all_time"
);

CREATE INDEX idx_metric_name ON metrics(metric_name);
CREATE INDEX idx_timestamp ON metrics(timestamp);
```

---

## 8. Deployment Architecture

### Local Development
```
Developer Machine
├── FastAPI backend (uvicorn)
├── Ollama (running locally or on separate machine)
└── SQLite database
```

### Docker Deployment
```
Docker Environment
├── Container 1: FastAPI + Application Code
├── Container 2: Ollama (if running containerized)
└── Shared Volume: SQLite database + config files
```

### docker-compose.yml Overview
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FIREWORKS_API_KEY=${FIREWORKS_API_KEY}
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_models:/root/.ollama
    command: serve
```

---

## 9. Error Handling & Recovery

### Error Categories

| Category | Example | Handling |
|----------|---------|----------|
| **Input Error** | Invalid prompt | Return 400 Bad Request |
| **Timeout** | Ollama takes >10s | Retry with fallback |
| **Rate Limit** | Fireworks 429 | Retry with fallback |
| **Server Error** | Fireworks 500 | Retry with fallback |
| **Connection Error** | No network | Retry up to max_retries |
| **Parse Error** | Invalid JSON response | Return error, don't retry |

### Retry Strategy
```
Algorithm:
  1. Try primary model
  2. If failure && retries < max_retries:
       Wait 1 second (exponential backoff)
       Try fallback model
  3. If fallback succeeds:
       Mark as "success_via_fallback"
       Log fallback usage
  4. If both fail:
       Return error to user
       Log failure
```

---

## 10. Monitoring & Observability

### Key Metrics to Track
1. Request volume (requests/minute)
2. Success rate (successful vs failed)
3. Fallback frequency (how often we use fallback)
4. Average latency (per model, per task type)
5. Token usage (total, per model)
6. Error rate (by error type)

### Logging
- All requests logged to SQLite
- All errors logged with full context
- Metrics calculated hourly/daily from logs

### Dashboard Queries (for analytics)
```sql
-- Total requests
SELECT COUNT(*) as total_requests FROM requests;

-- Success rate
SELECT 
  COUNT(CASE WHEN status = 'success' THEN 1 END) * 100.0 / COUNT(*) as success_rate_pct
FROM requests;

-- Token savings vs baseline
SELECT 
  SUM(tokens_used) as total_tokens_our_system,
  (SELECT SUM(tokens_used) * 1.3 FROM requests) as estimated_baseline_tokens  -- Assume 30% extra
FROM requests
WHERE status IN ('success', 'success_via_fallback');

-- Fallback frequency
SELECT 
  COUNT(CASE WHEN fallback_model_used = TRUE THEN 1 END) * 100.0 / COUNT(*) as fallback_pct
FROM requests;
```

---

## 11. Future Enhancements (Post-Hackathon)

1. **ML-based Routing:** Learn which model performs best per task
2. **Multi-language Support:** Support more languages than English
3. **Advanced Caching:** Cache responses for identical prompts
4. **Load Balancing:** Distribute across multiple instances
5. **Monitoring Dashboard:** Web UI for real-time metrics
6. **Custom Models:** Support user-provided local models

---

## 12. Assumptions & Constraints

### Assumptions
- Ollama is available locally or on accessible machine
- Fireworks API is always reachable
- Prompts are in English
- Task classification rules are accurate for test cases

### Constraints
- No authentication (not needed for hackathon)
- No rate limiting per user (single-user CLI tool)
- No persistent request history across deployments
- SQLite suitable for single-machine use

---

## 13. Reference Implementations

### Sample API Response Structure
```json
{
  "request_id": "req-abc123",
  "status": "success",
  "result": "Summary text here...",
  "metadata": {
    "task_type": "summarization",
    "primary_model": "ollama:qwen",
    "fallback_model_used": false,
    "final_model_used": "ollama:qwen",
    "latency_ms": 2340
  },
  "tokens": {
    "input": 500,
    "output": 187,
    "total": 687
  },
  "cost": {
    "usd": 0.0,
    "currency": "USD"
  }
}
```

### Sample Error Response
```json
{
  "request_id": "req-xyz789",
  "status": "failed",
  "error": "All models failed",
  "detail": "Primary (Mixtral): timeout. Fallback (Qwen-72B): 500 error.",
  "attempts": [
    {
      "model": "fireworks:mixtral",
      "status": "timeout",
      "error": "Request exceeded 15 second timeout"
    },
    {
      "model": "fireworks:qwen-72b",
      "status": "error",
      "error": "HTTP 500: Internal Server Error"
    }
  ]
}
```

---

## End of TDD
