# API Reference

Base URL: `http://localhost` (via Nginx proxy) or `http://localhost:8000` (direct, dev only)

All requests and responses use `application/json`.

---

## Authentication

API key authentication is **opt-in** and controlled by environment variables.

When enabled (`API_KEY_ENABLED=true`), include the key in every request:

```http
X-API-Key: your_api_key_here
```

---

## Rate Limiting

Default: **30 requests per minute per IP address**.

When exceeded, the API returns:

```http
HTTP 429 Too Many Requests
```

Configure via: `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_ENABLED` environment variables.

---

## Endpoints

### `GET /version`

Returns API version and environment information.

**Response `200`:**
```json
{
  "version": "1.0.0",
  "api_version": "v1",
  "environment": "production"
}
```

---

### `GET /health`

System health check verifying all downstream dependencies.

**Response `200` (healthy):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "ollama_local": "connected",
    "fireworks_cloud": "connected",
    "sqlite_metrics_db": "healthy"
  }
}
```

**Response `200` (degraded):**
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "services": {
    "ollama_local": "disconnected",
    "fireworks_cloud": "connected",
    "sqlite_metrics_db": "healthy"
  }
}
```

> **Note:** HTTP 200 is returned even when degraded. Check `status` field.

---

### `POST /process`

Route and execute a prompt through the intelligent model router.

**Request body:**
```json
{
  "prompt": "Write a Python function to reverse a string.",
  "task_type": "coding"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `prompt` | string | ✅ | 5–8000 characters |
| `task_type` | string | ❌ | One of: `math`, `coding`, `research`, `casual_chat` |

If `task_type` is omitted, the 3-tier classifier determines it automatically.

**Response `200`:**
```json
{
  "request_id": "3f5a1c2e-9b44-4f8d-a123-abc123def456",
  "status": "success",
  "result": "def reverse_string(s: str) -> str:\n    return s[::-1]",
  "metadata": {
    "task_type": "coding",
    "primary_model": "ollama:kimi-k2p7-code",
    "fallback_model_used": false,
    "final_model_used": "ollama:kimi-k2p7-code",
    "latency_ms": 1842
  },
  "tokens": {
    "input": 12,
    "output": 28,
    "total": 40
  },
  "cost": {
    "usd": 0.0000140,
    "currency": "USD"
  }
}
```

**Response `200` (fallback used):**
```json
{
  "status": "success_via_fallback",
  ...
  "metadata": {
    "fallback_model_used": true,
    "final_model_used": "ollama:gemma-4-31b-it",
    ...
  }
}
```

**Response `422` (validation error):**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "prompt"],
      "msg": "String should have at least 5 characters",
      "input": "hi"
    }
  ]
}
```

**Response `500` (all models failed):**
```json
{
  "request_id": "...",
  "status": "failed",
  "error": "All models in the fallback chain failed to respond.",
  "detail": "Primary failed: timeout. Fallback failed: connection refused.",
  "attempts": [
    {"model": "ollama:kimi-k2p7-code", "status": "failed", "error": "timeout"},
    {"model": "ollama:gemma-4-31b-it", "status": "failed", "error": "connection refused"}
  ]
}
```

**Response headers:**
```http
X-Request-ID: 3f5a1c2e-9b44-4f8d-a123-abc123def456
```

---

### `GET /metrics/summary`

Returns aggregated performance and cost-savings metrics from SQLite.

**Response `200`:**
```json
{
  "status": "success",
  "aggregated_metrics": {
    "total_requests": 142,
    "successful_requests": 139,
    "total_tokens": 42800,
    "total_cost": 0.018932,
    "avg_latency_ms": 1423.7,
    "fallback_count": 3,
    "baseline_cost_usd": 0.058240,
    "cost_saved_usd": 0.039308,
    "savings_pct": 67.5
  }
}
```

---

### `GET /metrics/models`

Returns per-model breakdown of request counts, latency, and cost.

**Response `200`:**
```json
{
  "status": "success",
  "models": [
    {
      "model": "ollama:minimax-m3",
      "request_count": 67,
      "avg_latency_ms": 892.4,
      "total_cost_usd": 0.000321,
      "total_tokens": 18200
    },
    {
      "model": "ollama:kimi-k2p7-code",
      "request_count": 42,
      "avg_latency_ms": 2104.1,
      "total_cost_usd": 0.005880,
      "total_tokens": 16800
    }
  ]
}
```

---

### `GET /metrics`

Prometheus-compatible metrics endpoint (plain text format).

Scraped automatically by Prometheus every 10 seconds.

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{handler="/process",method="POST",status_code="200"} 139.0
...
```

---

## cURL Examples

```bash
# Health check
curl http://localhost/api/health

# Submit a prompt (auto-classify)
curl -X POST http://localhost/api/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Solve for x: 2x + 6 = 20"}'

# Submit with manual task type
curl -X POST http://localhost/api/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello! How are you?", "task_type": "casual_chat"}'

# With API key (if enabled)
curl -X POST http://localhost/api/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key_here" \
  -d '{"prompt": "Implement bubble sort in Python."}'

# Get aggregated metrics
curl http://localhost/api/metrics/summary

# Get per-model breakdown
curl http://localhost/api/metrics/models

# API version
curl http://localhost/api/version
```

---

## Interactive API Docs

- **Swagger UI**: `http://localhost/api/docs`
- **ReDoc**: `http://localhost/api/redoc`
- **OpenAPI JSON**: `http://localhost/api/openapi.json`
