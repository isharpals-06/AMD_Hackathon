# Developer Setup Guide
## Multi-Model Fallback Router

**Last Updated:** July 2026

---

## 1. Prerequisites

### System Requirements
- **OS:** macOS, Linux, or Windows (with WSL2)
- **Python:** 3.10 or higher
- **Docker:** (optional, for containerized deployment)
- **RAM:** 8GB minimum (4GB if not running Ollama locally)
- **Disk:** 10GB free (for Ollama models)

### Required Tools
- Git
- Python 3.10+ with pip
- Curl (or Postman for API testing)

---

## 2. Step-by-Step Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/your-team/multi-model-router.git
cd multi-model-router
```

### Step 2: Create Python Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate venv
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -m fastapi --version
```

### Step 4: Install & Configure Ollama

#### Option A: Run Ollama Locally

**Installation:**
```bash
# macOS (Homebrew)
brew install ollama

# Linux (Ubuntu/Debian)
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download

# Start Ollama service
ollama serve
```

**In a new terminal, download Qwen model:**
```bash
ollama pull qwen:7b
```

**Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
# Should return list of available models
```

#### Option B: Use Remote Ollama
If you don't want to run Ollama locally:
1. Set `OLLAMA_URL=http://remote-host:11434` in `.env`
2. Ensure the remote Ollama instance is accessible

### Step 5: Set Up Fireworks API

**1. Create Fireworks Account**
- Go to https://fireworks.ai
- Sign up and create account
- Create API key in settings

**2. Add API Key to .env**
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your Fireworks API key
nano .env
# OR
code .env
```

**.env file:**
```
FIREWORKS_API_KEY=your_api_key_here
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
DATABASE_URL=sqlite:///./data/metrics.db
CHROMADB_DIR=./data/chromadb
DEBUG=False
```

**3. Test Fireworks API**
```bash
python scripts/test_fireworks.py
# Should output: "Successfully connected to Fireworks API"
```

### Step 6: Initialize Database
```bash
python scripts/init_db.py
# Creates SQLite database and tables
```

### Step 7: Verify All Integrations
```bash
python scripts/health_check.py
```

**Expected output:**
```
✓ FastAPI
✓ Ollama (http://localhost:11434)
✓ Fireworks API
✓ Database (./data/metrics.db)
All systems operational!
```

---

## 3. Project Structure

```
multi-model-router/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # Pydantic models (request/response schemas)
│   ├── routes.py               # API endpoints
│   ├── services/
│   │   ├── classifier.py       # Task classification logic
│   │   ├── router.py           # Routing decision engine
│   │   ├── executor.py         # Model execution
│   │   ├── ollama_client.py    # Ollama integration
│   │   ├── fireworks_client.py # Fireworks API integration
│   │   └── token_counter.py    # Token counting & cost calc
│   ├── database.py             # SQLite connection & queries
│   ├── config.py               # Configuration (load from .env)
│   └── utils.py                # Helper functions
├── tests/
│   ├── test_classifier.py
│   ├── test_router.py
│   ├── test_executor.py
│   ├── test_api.py
│   └── fixtures.py             # Test data
├── scripts/
│   ├── test_fireworks.py       # Test Fireworks connection
│   ├── test_ollama.py          # Test Ollama connection
│   ├── health_check.py         # System health check
│   ├── init_db.py              # Initialize database
│   └── benchmark.py            # Run benchmarks
├── data/
│   └── metrics.db              # SQLite database (auto-created)
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose config
├── README.md                   # Project readme
└── PRD.md                      # Product requirements document
```

---

## 4. Running the Application

### Development Mode (with auto-reload)
```bash
# Activate venv first
source venv/bin/activate

# Run FastAPI with uvicorn (auto-reload on code changes)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [PID]
INFO:     Application startup complete
```

### Access API
```bash
# Health check
curl http://localhost:8000/health

# Process a request
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize quantum computing", "task_type": "summarization"}'
```

### CLI Interface (Alternative)
```bash
# If using Click CLI wrapper:
python -m app.cli --prompt "Your prompt here" --task-type summarization
```

---

## 5. Testing

### Run All Tests
```bash
# Activate venv
source venv/bin/activate

# Run tests
pytest -v

# Run with coverage
pytest --cov=app tests/
```

### Run Specific Test
```bash
pytest tests/test_classifier.py -v
pytest tests/test_router.py::test_routing_summarization -v
```

### Run Manual Tests
```bash
# Test individual components
python scripts/test_ollama.py      # Test Ollama connection
python scripts/test_fireworks.py   # Test Fireworks API
python scripts/health_check.py     # System health
```

### Test Cases Included
```
tests/
├── test_classifier.py
│   ├── test_classify_summarization
│   ├── test_classify_coding
│   ├── test_classify_code_review
│   ├── test_classify_edge_cases
│   └── test_classifier_confidence
│
├── test_router.py
│   ├── test_route_summarization_to_ollama
│   ├── test_route_coding_to_mixtral
│   ├── test_route_code_review_to_mixtral
│   └── test_route_fallback_logic
│
├── test_executor.py
│   ├── test_execute_success
│   ├── test_execute_with_timeout
│   ├── test_execute_with_fallback
│   ├── test_execute_api_error
│   └── test_token_counting
│
└── test_api.py
    ├── test_post_process_success
    ├── test_post_process_validation_error
    ├── test_get_metrics
    ├── test_get_requests
    └── test_get_health
```

---

## 6. Development Workflow

### Making Code Changes

**1. Create a branch**
```bash
git checkout -b feature/your-feature-name
```

**2. Make changes**
```bash
# Edit files
nano app/services/classifier.py
```

**3. Run tests locally**
```bash
pytest -v
```

**4. Run the app to test manually**
```bash
uvicorn app.main:app --reload
# In another terminal: curl http://localhost:8000/process ...
```

**5. Commit and push**
```bash
git add .
git commit -m "Add feature X"
git push origin feature/your-feature-name
```

**6. Create pull request**
- Open PR on GitHub
- Wait for CI/CD to pass
- Get code review approval
- Merge to main

### Code Style & Linting

**Check code style**
```bash
# Run black (code formatter)
black app/ tests/

# Run flake8 (linter)
flake8 app/ tests/

# Run mypy (type checker)
mypy app/
```

**Auto-format code**
```bash
black app/ tests/ --line-length 100
```

---

## 7. Environment Variables

### .env File
```
# API Configuration
DEBUG=True                              # False in production
PORT=8000
HOST=0.0.0.0

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_TIMEOUT=10

# ChromaDB Configuration
CHROMADB_DIR=./data/chromadb

# Fireworks Configuration
FIREWORKS_API_KEY=your_api_key_here
FIREWORKS_TIMEOUT=15

# Database Configuration
DATABASE_URL=sqlite:///./data/metrics.db

# Logging
LOG_LEVEL=INFO                         # DEBUG, INFO, WARNING, ERROR
```

### Loading Environment Variables
```python
# In app/config.py
from dotenv import load_dotenv
import os

load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
```

---

## 8. Troubleshooting

### Issue: "Connection refused" (Ollama)
**Problem:** Ollama is not running
```bash
# Solution: Start Ollama in a separate terminal
ollama serve

# Or check if Ollama process is running
ps aux | grep ollama
```

### Issue: "API Key not found" (Fireworks)
**Problem:** FIREWORKS_API_KEY not in .env
```bash
# Solution: Add API key to .env
nano .env
# Add: FIREWORKS_API_KEY=your_key_here
```

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Problem:** Dependencies not installed
```bash
# Solution: Install requirements
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Permission denied" (Linux/macOS)
**Problem:** Venv script not executable
```bash
# Solution: Make script executable
chmod +x venv/bin/activate
```

### Issue: Requests timing out
**Problem:** Ollama or Fireworks too slow
```bash
# Solution 1: Increase timeout in .env
OLLAMA_TIMEOUT=20
FIREWORKS_TIMEOUT=30

# Solution 2: Check network connection
ping ollama_host
ping api.fireworks.ai
```

---

## 9. Docker Development

### Build Docker Image
```bash
docker build -t multi-model-router .
```

### Run Container Locally
```bash
docker run -p 8000:8000 \
  -e FIREWORKS_API_KEY=your_key \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  multi-model-router
```

### Using Docker Compose (Recommended)
```bash
# Start all services
docker-compose up

# Run in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api
```

**docker-compose.yml includes:**
- FastAPI app
- Ollama service (optional)
- SQLite database
- Network configuration

---

## 10. Database Management

### View Database
```bash
# Install SQLite client
# macOS: brew install sqlite
# Linux: apt-get install sqlite3

# Open database
sqlite3 data/metrics.db

# List tables
.tables

# Query requests
SELECT request_id, task_type, status, tokens_used FROM requests LIMIT 10;

# Calculate metrics
SELECT COUNT(*) as total, 
       SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successful,
       ROUND(SUM(tokens_used), 2) as total_tokens
FROM requests;
```

### Reset Database
```bash
# Delete database file
rm data/metrics.db

# Reinitialize
python scripts/init_db.py
```

### Database Backups
```bash
# Backup database
cp data/metrics.db data/metrics.db.backup

# Restore from backup
cp data/metrics.db.backup data/metrics.db
```

---

## 11. Performance Tips

### Optimize for Development Speed
```python
# In .env for development
DEBUG=True
OLLAMA_TIMEOUT=5  # Shorter timeout for faster feedback

# In config.py, reduce token counting overhead:
CACHE_TOKENS=True  # Cache token counts for identical prompts
```

### Debugging
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Routing decision: {task_type} -> {model}")
```

### Profiling
```bash
# Install profiler
pip install py-spy

# Profile running app
py-spy record -o profile.svg -- uvicorn app.main:app
```

---

## 12. Useful Commands Reference

```bash
# Activate venv
source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Run app
uvicorn app.main:app --reload

# Run tests
pytest -v

# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type check
mypy app/

# Health check
python scripts/health_check.py

# Benchmark
python scripts/benchmark.py

# Docker
docker-compose up
docker-compose logs -f api
docker-compose down
```

---

## 13. When You're Done Developing

### Before Committing
```bash
# Format code
black app/ tests/

# Run linter
flake8 app/ tests/

# Run type checker
mypy app/

# Run all tests
pytest -v --cov=app

# Run health check
python scripts/health_check.py
```

### Pre-Submission Checklist
- [ ] All tests passing
- [ ] No linting errors
- [ ] No type errors
- [ ] Code is formatted
- [ ] .env.example updated (if new env vars)
- [ ] README.md updated
- [ ] Docker image builds successfully
- [ ] Health check passes

---

## End of Developer Setup Guide
