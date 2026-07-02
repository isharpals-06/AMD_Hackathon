# API Documentation
## Multi-Model Fallback Router

**Version:** 1.0  
**Base URL:** `http://localhost:8000` (local) or `http://{app-url}:8000` (deployed)  
**Authentication:** None (hackathon, single-user tool)  

---

## 1. API Overview

### Available Endpoints
```
POST   /process              Process a request (main endpoint)
GET    /health              Health check
GET    /metrics             Get aggregated metrics
GET    /requests            List all requests (with filters)
GET    /requests/{id}       Get specific request details
```

---

## 2. Main Endpoint: Process Request

### Endpoint: `POST /process`

**Description:** Submit a prompt for processing through the intelligent router.

**Request Format:**
```json
{
  "prompt": "string (required, 10-50,000 characters)",
  "task_type": "string (optional, auto-detected if not provided)"
}
```

**Task Types:**
- `"summarization"` - Summarize text, articles, documents
- `"coding"` - Write, generate, or explain code
- `"code_review"` - Review code for issues, security, performance
- `"general"` - Anything else (defaults to high-quality model)

**Success Response (200 OK):**
```json
{
  "request_id": "req-550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "result": "The article discusses how quantum computing could revolutionize drug discovery...",
  "metadata": {
    "task_type": "summarization",
    "primary_model": "ollama:qwen",
    "fallback_model_used": false,
    "final_model_used": "ollama:qwen",
    "latency_ms": 2340,
    "timestamp": "2026-07-10T15:30:45.123Z"
  },
  "tokens": {
    "input_tokens": 500,
    "output_tokens": 187,
    "total_tokens": 687
  },
  "cost": {
    "usd": 0.0,
    "currency": "USD",
    "note": "Local Ollama inference is free"
  }
}
```

**Failure Response (200 OK, but status=failed):**
```json
{
  "request_id": "req-abc123def456",
  "status": "failed",
  "error": "All models failed",
  "error_detail": "Primary model (Fireworks Mixtral) timed out after 15 seconds. Fallback (Qwen-72B) returned HTTP 500.",
  "metadata": {
    "task_type": "coding",
    "primary_model": "fireworks:mixtral",
    "fallback_model_used": true,
    "final_model_used": "fireworks:qwen-72b",
    "latency_ms": 16000,
    "timestamp": "2026-07-10T15:32:10.456Z"
  },
  "attempts": [
    {
      "model": "fireworks:mixtral",
      "status": "timeout",
      "error": "Request exceeded timeout of 15 seconds"
    },
    {
      "model": "fireworks:qwen-72b",
      "status": "error",
      "http_status": 500,
      "error": "Internal Server Error"
    }
  ]
}
```

**Validation Error (400 Bad Request):**
```json
{
  "error": "Validation Error",
  "details": [
    {
      "field": "prompt",
      "error": "Prompt must be between 10 and 50,000 characters"
    }
  ]
}
```

### Example Requests

#### Example 1: Summarization (Auto-Detected)
**Request:**
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Summarize this article: The rapid advancement of artificial intelligence has led to significant breakthroughs in healthcare, finance, and education sectors globally. Machine learning models trained on large datasets can now predict disease outcomes with 95% accuracy..."
  }'
```

**Response:**
```json
{
  "request_id": "req-001",
  "status": "success",
  "result": "AI is advancing rapidly across multiple sectors (healthcare, finance, education) with significant breakthroughs. ML models now achieve 95% accuracy in disease prediction...",
  "metadata": {
    "task_type": "summarization",
    "primary_model": "ollama:qwen",
    "final_model_used": "ollama:qwen",
    "latency_ms": 1840
  },
  "tokens": {
    "total_tokens": 125
  },
  "cost": { "usd": 0.0 }
}
```

#### Example 2: Coding with Explicit Task Type
**Request:**
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function that implements a binary search tree with insert, delete, and search operations",
    "task_type": "coding"
  }'
```

**Response:**
```json
{
  "request_id": "req-002",
  "status": "success",
  "result": "class Node:\n    def __init__(self, val):\n        self.val = val\n        self.left = None\n        self.right = None\n\nclass BST:\n    def __init__(self):\n        self.root = None\n    \n    def insert(self, val):\n        if not self.root:\n            self.root = Node(val)\n        else:\n            self._insert_recursive(self.root, val)\n    \n    def _insert_recursive(self, node, val):\n        if val < node.val:\n            if node.left is None:\n                node.left = Node(val)\n            else:\n                self._insert_recursive(node.left, val)\n        else:\n            if node.right is None:\n                node.right = Node(val)\n            else:\n                self._insert_recursive(node.right, val)\n    \n    def search(self, val):\n        return self._search_recursive(self.root, val)\n    \n    def _search_recursive(self, node, val):\n        if node is None:\n            return False\n        if val == node.val:\n            return True\n        elif val < node.val:\n            return self._search_recursive(node.left, val)\n        else:\n            return self._search_recursive(node.right, val)",
  "metadata": {
    "task_type": "coding",
    "primary_model": "fireworks:mixtral",
    "final_model_used": "fireworks:mixtral",
    "latency_ms": 8200
  },
  "tokens": {
    "total_tokens": 450
  },
  "cost": { "usd": 0.00068 }
}
```

#### Example 3: Code Review with Fallback
**Request:**
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Review this Go function for security issues: func getUserData(userID string, db *sql.DB) (string, error) { query := \"SELECT email FROM users WHERE id=\" + userID; rows, err := db.Query(query); ... }",
    "task_type": "code_review"
  }'
```

**Response (with fallback):**
```json
{
  "request_id": "req-003",
  "status": "success",
  "result": "SECURITY ISSUES FOUND:\n\n1. **SQL Injection Vulnerability** (CRITICAL)\n   - The query is constructed by string concatenation\n   - Attacker could pass userID like: \"1; DROP TABLE users; --\"\n   - FIX: Use parameterized queries\n   \n2. **Missing Error Handling** (HIGH)\n   - No validation of userID parameter\n   - Error messages could leak system information\n   \nRECOMMENDED FIX:\n```go\nfunc getUserData(userID string, db *sql.DB) (string, error) {\n    if userID == \"\" {\n        return \"\", errors.New(\"invalid user ID\")\n    }\n    query := \"SELECT email FROM users WHERE id = $1\"\n    var email string\n    err := db.QueryRow(query, userID).Scan(&email)\n    return email, err\n}\n```",
  "metadata": {
    "task_type": "code_review",
    "primary_model": "fireworks:mixtral",
    "fallback_model_used": false,
    "final_model_used": "fireworks:mixtral",
    "latency_ms": 5600
  },
  "tokens": {
    "total_tokens": 380
  },
  "cost": { "usd": 0.00057 }
}
```

---

## 3. Health Check Endpoint

### Endpoint: `GET /health`

**Description:** Check if the API is running and all integrations are available.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-07-10T15:35:00.000Z",
  "integrations": {
    "ollama": {
      "status": "available",
      "url": "http://localhost:11434",
      "models": ["qwen:7b"]
    },
    "fireworks": {
      "status": "available",
      "api_key_configured": true
    },
    "database": {
      "status": "available",
      "path": "/app/data/metrics.db"
    }
  }
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "timestamp": "2026-07-10T15:35:00.000Z",
  "integrations": {
    "ollama": {
      "status": "unavailable",
      "error": "Connection refused at http://localhost:11434"
    },
    "fireworks": {
      "status": "available"
    },
    "database": {
      "status": "available"
    }
  },
  "message": "Ollama is not reachable. Summarization requests may fail."
}
```

---

## 4. Metrics Endpoint

### Endpoint: `GET /metrics`

**Description:** Get aggregated metrics across all processed requests.

**Query Parameters:**
- `period` (optional): `"1h"`, `"1d"`, `"all_time"` (default: `"all_time"`)
- `task_type` (optional): Filter by task type
- `model` (optional): Filter by model

**Response (200 OK):**
```json
{
  "period": "all_time",
  "aggregated_metrics": {
    "total_requests": 15,
    "successful_requests": 13,
    "failed_requests": 2,
    "success_rate_pct": 86.67,
    "total_tokens_used": 8920,
    "total_cost_usd": 0.01245,
    "average_latency_ms": 4230,
    "fallback_usage_pct": 13.33
  },
  "by_task_type": {
    "summarization": {
      "requests": 5,
      "success_rate_pct": 100,
      "total_tokens": 1250,
      "average_latency_ms": 2400
    },
    "coding": {
      "requests": 6,
      "success_rate_pct": 83.33,
      "total_tokens": 5600,
      "average_latency_ms": 8100
    },
    "code_review": {
      "requests": 4,
      "success_rate_pct": 75,
      "total_tokens": 2070,
      "average_latency_ms": 5200
    }
  },
  "by_model": {
    "ollama:qwen": {
      "requests": 5,
      "total_tokens": 1250,
      "cost_usd": 0,
      "success_rate_pct": 100
    },
    "fireworks:mixtral": {
      "requests": 8,
      "total_tokens": 5600,
      "cost_usd": 0.00840,
      "success_rate_pct": 87.5
    },
    "fireworks:qwen-72b": {
      "requests": 2,
      "total_tokens": 2070,
      "cost_usd": 0.00405,
      "success_rate_pct": 50
    }
  }
}
```

**Example Request:**
```bash
curl http://localhost:8000/metrics?period=1d&task_type=coding
```

---

## 5. List Requests Endpoint

### Endpoint: `GET /requests`

**Description:** List all processed requests with optional filters.

**Query Parameters:**
- `limit` (optional, default: 50): Max results to return
- `offset` (optional, default: 0): Pagination offset
- `task_type` (optional): Filter by task type
- `status` (optional): Filter by status (`success`, `failed`, `success_via_fallback`)
- `sort_by` (optional): `timestamp`, `tokens`, `latency` (default: `timestamp`)
- `sort_order` (optional): `asc`, `desc` (default: `desc`)

**Response (200 OK):**
```json
{
  "total_count": 15,
  "limit": 50,
  "offset": 0,
  "requests": [
    {
      "request_id": "req-001",
      "timestamp": "2026-07-10T15:30:45.123Z",
      "task_type": "summarization",
      "status": "success",
      "final_model_used": "ollama:qwen",
      "tokens_used": 687,
      "cost_usd": 0.0,
      "latency_ms": 2340,
      "prompt_preview": "Summarize this article: The rapid advancement of...",
      "response_preview": "AI is advancing rapidly across multiple sectors..."
    },
    {
      "request_id": "req-002",
      "timestamp": "2026-07-10T15:32:10.456Z",
      "task_type": "coding",
      "status": "success",
      "final_model_used": "fireworks:mixtral",
      "tokens_used": 450,
      "cost_usd": 0.00068,
      "latency_ms": 8200,
      "fallback_used": false
    }
  ]
}
```

**Example Request:**
```bash
curl "http://localhost:8000/requests?task_type=summarization&status=success&limit=10"
```

---

## 6. Get Request Details Endpoint

### Endpoint: `GET /requests/{request_id}`

**Description:** Get full details of a specific request.

**Path Parameters:**
- `request_id` (required): The UUID of the request

**Response (200 OK):**
```json
{
  "request_id": "req-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-07-10T15:30:45.123Z",
  "task_type": "summarization",
  "status": "success",
  "prompt": "Summarize this article: The rapid advancement of artificial intelligence...",
  "result": "AI is advancing rapidly across multiple sectors (healthcare, finance, education)...",
  "metadata": {
    "primary_model": "ollama:qwen",
    "fallback_model_used": false,
    "final_model_used": "ollama:qwen",
    "latency_ms": 2340
  },
  "tokens": {
    "input_tokens": 500,
    "output_tokens": 187,
    "total_tokens": 687
  },
  "cost": {
    "usd": 0.0
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": "Not Found",
  "message": "Request with ID 'req-invalid' not found"
}
```

**Example Request:**
```bash
curl http://localhost:8000/requests/req-550e8400-e29b-41d4-a716-446655440000
```

---

## 7. Error Responses

### Error Response Format
All errors follow this structure:
```json
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "request_id": "req-xxx (if applicable)",
  "timestamp": "ISO-8601 timestamp"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| `200` | OK (request processed, may be success or failure) | See above |
| `400` | Bad Request (validation error) | Invalid prompt length |
| `404` | Not Found | Request ID doesn't exist |
| `408` | Request Timeout | Both models timed out |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |
| `503` | Service Unavailable | Ollama not reachable |

### Common Error Scenarios

#### Validation Error (400)
**Request:**
```bash
curl -X POST http://localhost:8000/process \
  -d '{"prompt": "short"}' \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "error": "Validation Error",
  "message": "Invalid input",
  "details": [
    {
      "field": "prompt",
      "error": "Prompt must be at least 10 characters"
    }
  ],
  "status_code": 400
}
```

#### Service Unavailable (503)
```json
{
  "error": "Service Unavailable",
  "message": "Cannot reach required services",
  "details": {
    "ollama": "Connection refused",
    "fireworks": "available"
  },
  "status_code": 503
}
```

#### Request Timeout (408)
```json
{
  "error": "Request Timeout",
  "message": "Both primary and fallback models failed or timed out",
  "attempts": [
    {
      "model": "fireworks:mixtral",
      "status": "timeout",
      "latency_ms": 15000
    },
    {
      "model": "fireworks:qwen-72b",
      "status": "timeout",
      "latency_ms": 15000
    }
  ],
  "status_code": 408
}
```

---

## 8. Rate Limiting & Quotas

### Current Limits (Hackathon)
- No per-user rate limiting (single-user CLI tool)
- Fireworks API: ~100 requests/minute on free tier
- Ollama: Limited by local hardware

### Future Considerations
- Implement per-IP rate limiting if needed
- Queue requests if quota exceeded
- Implement request batching for efficiency

---

## 9. Authentication & Security

### Current Implementation
- No authentication required (hackathon)
- Fireworks API key passed via environment variable
- All requests logged locally

### Future Enhancements
- API key authentication for multi-user deployments
- Request signing to prevent tampering
- Rate limiting per API key
- Usage tracking and billing

---

## 10. Versioning

### API Versioning Strategy
- Current version: `v1` (not required in URL for hackathon)
- Future versions: `/api/v2/...`
- Breaking changes will bump major version

### Backward Compatibility
- Will maintain backward compatibility within v1
- Deprecated fields will be marked
- Full migration guide provided before version changes

---

## 11. CLI Interface (Alternative to HTTP API)

While the API is HTTP-based, a CLI wrapper is provided for convenience:

```bash
# Submit a request
./router.py --prompt "Summarize this article..." --task-type summarization

# Get metrics
./router.py --metrics

# List recent requests
./router.py --list-requests --limit 10

# Get request details
./router.py --get-request <request-id>
```

---

## 12. SDK / Client Libraries

### Python Client (Example)
```python
from router_client import RouterClient

client = RouterClient(base_url="http://localhost:8000")

# Process a request
response = client.process(
    prompt="Summarize this article...",
    task_type="summarization"
)

print(f"Result: {response.result}")
print(f"Tokens: {response.tokens.total_tokens}")
print(f"Cost: ${response.cost.usd}")

# Get metrics
metrics = client.get_metrics(period="1d")
print(f"Success rate: {metrics.success_rate_pct}%")
```

### JavaScript/Node.js Client (Example)
```javascript
const RouterClient = require('router-client');

const client = new RouterClient({ baseUrl: 'http://localhost:8000' });

const response = await client.process({
  prompt: 'Summarize this article...',
  taskType: 'summarization'
});

console.log(`Result: ${response.result}`);
console.log(`Tokens: ${response.tokens.totalTokens}`);
```

---

## 13. Testing the API

### Using cURL
```bash
# Simple request
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize quantum computing in 50 words", "task_type": "summarization"}'

# With pretty output
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "..."}' | jq .
```

### Using Postman
1. Create new POST request to `http://localhost:8000/process`
2. Set header: `Content-Type: application/json`
3. Set body:
   ```json
   {
     "prompt": "Your prompt here",
     "task_type": "summarization"
   }
   ```
4. Send request

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/process",
    json={
        "prompt": "Summarize this...",
        "task_type": "summarization"
    }
)

print(response.json())
```

---

## End of API Documentation
