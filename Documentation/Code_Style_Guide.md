# Code Style Guide & Standards
## Multi-Model Fallback Router

**Version:** 1.0  
**Language:** Python 3.10+  
**Framework:** FastAPI  

---

## 1. Python Code Style

### 1.1 Follow PEP 8

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) conventions.

**Tools:**
- **black:** Code formatter (enforced)
- **flake8:** Linter
- **mypy:** Type checker

**Setup:**
```bash
pip install black flake8 mypy
black app/ tests/
flake8 app/ tests/
mypy app/
```

### 1.2 Line Length

- **Maximum:** 100 characters (per black's default)
- **Rationale:** Readable on most screens, fits in code reviews

```python
# ✓ Good
def process_request(
    prompt: str,
    task_type: str = "general",
    timeout: int = 10
) -> ProcessResponse:
    """Process a user request."""
    pass

# ✗ Bad
def process_request(prompt: str, task_type: str = "general", timeout: int = 10) -> ProcessResponse:
```

### 1.3 Indentation

- **Use:** 4 spaces (never tabs)
- **Block structure:** Consistent indentation for all blocks

```python
# ✓ Good
if task_type == "summarization":
    model = "ollama:qwen"
    timeout = 10
else:
    model = "fireworks:mixtral"
    timeout = 15

# ✗ Bad
if task_type == "summarization":
  model = "ollama:qwen"  # 2 spaces (wrong)
```

### 1.4 Imports

**Order:**
1. Standard library imports
2. Third-party imports
3. Local imports

Separate groups with blank lines.

```python
# ✓ Good
import os
from typing import Dict, List

import httpx
import pydantic
from fastapi import FastAPI

from app.services.classifier import TaskClassifier
from app.database import Database

# ✗ Bad
from app.services.classifier import TaskClassifier
import os
from fastapi import FastAPI
from app.database import Database
import httpx
```

### 1.5 Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| **Functions** | `snake_case` | `classify_task()`, `get_routing()` |
| **Variables** | `snake_case` | `task_type`, `max_retries`, `primary_model` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| **Classes** | `PascalCase` | `TaskClassifier`, `RoutingEngine` |
| **Private members** | `_leading_underscore` | `_internal_cache`, `_parse_response()` |

```python
# ✓ Good
MAX_PROMPT_LENGTH = 50000
DEFAULT_TIMEOUT = 10

class TaskClassifier:
    def __init__(self):
        self._rules = {}
    
    def classify(self, prompt: str) -> str:
        task_type = self._determine_type(prompt)
        return task_type
    
    def _determine_type(self, prompt: str) -> str:
        # Internal method
        pass

# ✗ Bad
MaxPromptLength = 50000  # Wrong case
DefaultTimeOut = 10  # Wrong case
def classifyTask(prompt):  # Wrong naming
    taskType = ...  # Wrong case
```

---

## 2. Type Hints

### 2.1 Always Use Type Hints

```python
# ✓ Good
def process_request(
    prompt: str,
    task_type: str,
    timeout: int = 10
) -> ProcessResponse:
    """Process a user request."""
    pass

# ✗ Bad
def process_request(prompt, task_type, timeout=10):
    """Process a user request."""
    pass
```

### 2.2 Common Type Hints

```python
from typing import Dict, List, Optional, Tuple, Union

# Strings and numbers
name: str
age: int
salary: float
is_active: bool

# Collections
tags: List[str]
config: Dict[str, int]
coordinates: Tuple[float, float]

# Optional
optional_value: Optional[str] = None  # or str | None
fallback_model: Optional[str] = None

# Union
response: Union[str, dict]

# Complex types
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
```

### 2.3 Function Return Types

```python
# ✓ Good
def classify_task(prompt: str) -> str:
    """Classify task type."""
    return "summarization"

def get_routing(task_type: str) -> Dict[str, Any]:
    """Get routing configuration."""
    return {"primary": "ollama:qwen", "timeout": 10}

def validate_prompt(prompt: str) -> bool:
    """Check if prompt is valid."""
    return len(prompt) >= 10

# ✗ Bad
def classify_task(prompt):
    return "summarization"
```

---

## 3. Docstrings

### 3.1 Use Google-Style Docstrings

```python
def process_request(
    prompt: str,
    task_type: Optional[str] = None,
    timeout: int = 10
) -> ProcessResponse:
    """
    Process a user request through the intelligent router.

    Classifies the task type, selects an appropriate model,
    and executes the request with fallback support.

    Args:
        prompt: The user's input prompt (10-50,000 characters)
        task_type: Optional task type. Auto-detected if not provided.
                  Options: "summarization", "coding", "code_review", "general"
        timeout: Request timeout in seconds (default: 10)

    Returns:
        ProcessResponse: Contains result, tokens used, model used, latency

    Raises:
        ValueError: If prompt is too short or too long
        ConnectionError: If all models fail to respond

    Examples:
        >>> response = process_request("Summarize this article...")
        >>> print(response.result)
        "The article discusses..."
    """
    pass
```

### 3.2 Class Docstrings

```python
class TaskClassifier:
    """
    Classifies user requests into task types.

    Uses regex-based rules to classify prompts into:
    - summarization: Text summarization tasks
    - coding: Code generation or modification
    - code_review: Code review requests
    - general: Any other task type (fallback)

    Attributes:
        rules (Dict[str, str]): Mapping of keywords to task types
        confidence (float): Classification confidence score (0-1)
    """

    def __init__(self):
        """Initialize the classifier with default rules."""
        self.rules = self._load_rules()

    def classify(self, prompt: str) -> str:
        """
        Classify a prompt into a task type.

        Args:
            prompt: The user's prompt

        Returns:
            str: Task type ("summarization", "coding", "code_review", "general")
        """
        pass
```

### 3.3 Module Docstrings

```python
"""
Task classification service for the Multi-Model Router.

This module provides functionality to classify user requests
into task types based on prompt analysis.

Classes:
    TaskClassifier: Main classification service

Functions:
    extract_keywords: Extract keywords from prompt
"""
```

---

## 4. File Organization

### 4.1 Project Structure

```
app/
├── __init__.py                 # Package init
├── main.py                     # FastAPI app entry point
├── config.py                   # Configuration (env vars, constants)
├── models.py                   # Pydantic models (request/response schemas)
├── routes.py                   # API routes (@app.post, @app.get, etc.)
├── database.py                 # Database connection & utilities
├── exceptions.py               # Custom exceptions
├── utils.py                    # Helper functions
└── services/                   # Business logic
    ├── __init__.py
    ├── classifier.py           # Task classification
    ├── router.py               # Routing decision engine
    ├── executor.py             # Model execution
    ├── ollama_client.py        # Ollama API client
    ├── fireworks_client.py     # Fireworks API client
    └── token_counter.py        # Token counting & cost calc
```

### 4.2 File Size Guidelines

- **Max file size:** 500 lines (split if larger)
- **Max function size:** 50 lines (refactor if larger)
- **Classes:** Keep cohesive, <200 lines per class

```python
# ✗ Bad: Single huge file
# app/services.py (5000 lines)

# ✓ Good: Modular files
# app/services/classifier.py (150 lines)
# app/services/router.py (120 lines)
# app/services/executor.py (180 lines)
```

---

## 5. Testing Standards

### 5.1 Test File Organization

```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures
├── fixtures.py                 # Test data
├── test_classifier.py          # Unit tests for classifier
├── test_router.py              # Unit tests for router
├── test_executor.py            # Unit tests for executor
├── test_integration.py         # Integration tests
├── test_api.py                 # API endpoint tests
└── test_acceptance.py          # End-to-end acceptance tests
```

### 5.2 Test Naming

```python
# ✓ Good: Descriptive test names
def test_classify_summarization_basic():
    pass

def test_route_coding_to_mixtral():
    pass

def test_executor_handles_timeout_gracefully():
    pass

# ✗ Bad: Vague test names
def test_classifier():
    pass

def test_route():
    pass

def test_error():
    pass
```

### 5.3 Test Structure (Arrange-Act-Assert)

```python
def test_classify_summarization():
    """Test summarization classification."""
    # Arrange: Set up test data
    classifier = TaskClassifier()
    prompt = "Summarize this article"
    
    # Act: Execute the function
    result = classifier.classify(prompt)
    
    # Assert: Verify results
    assert result == "summarization"
    assert isinstance(result, str)
```

### 5.4 Test Coverage

- **Target:** 80%+ code coverage
- **Critical paths:** 100% coverage required
- **Run coverage:** `pytest --cov=app tests/`

---

## 6. Error Handling

### 6.1 Use Custom Exceptions

```python
# app/exceptions.py
class RouterException(Exception):
    """Base exception for router."""
    pass

class ModelNotAvailableError(RouterException):
    """Raised when a model is not available."""
    pass

class InvalidPromptError(RouterException):
    """Raised when prompt validation fails."""
    pass

class TimeoutError(RouterException):
    """Raised when request times out."""
    pass
```

### 6.2 Handle Exceptions Appropriately

```python
# ✓ Good: Specific exception handling
try:
    response = await call_ollama(prompt)
except httpx.TimeoutException:
    logger.warning("Ollama timed out, trying fallback")
    response = await call_fireworks(prompt)
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise ModelNotAvailableError("No models available")

# ✗ Bad: Catching all exceptions
try:
    response = await call_ollama(prompt)
except Exception:
    pass  # Swallows real errors
```

### 6.3 Logging Errors

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = execute_model(prompt)
except TimeoutException as e:
    logger.error(
        f"Model timeout: {e}",
        extra={
            "model": "ollama:qwen",
            "timeout_seconds": 10,
            "request_id": request_id
        }
    )
    raise
```

---

## 7. API Documentation

### 7.1 FastAPI Route Documentation

```python
from fastapi import FastAPI
from app.models import ProcessRequest, ProcessResponse

app = FastAPI(
    title="Multi-Model Router",
    description="Intelligent routing system for AI models",
    version="1.0.0"
)

@app.post(
    "/process",
    response_model=ProcessResponse,
    summary="Process a request",
    description="Submit a prompt for processing through the intelligent router"
)
async def process_request(request: ProcessRequest) -> ProcessResponse:
    """
    Process a user request.

    - **prompt**: User's input (10-50,000 characters)
    - **task_type**: Optional task type (auto-detected if not provided)

    Returns a ProcessResponse with result, tokens, cost, and metadata.
    """
    pass
```

### 7.2 Pydantic Model Documentation

```python
from pydantic import BaseModel, Field

class ProcessRequest(BaseModel):
    """Request to process through the router."""
    
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="The user's prompt"
    )
    task_type: Optional[str] = Field(
        None,
        description="Task type: 'summarization', 'coding', 'code_review', 'general'"
    )

class ProcessResponse(BaseModel):
    """Response from processing."""
    
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="'success' or 'failed'")
    result: str = Field(..., description="The model's output")
    tokens: TokenInfo = Field(..., description="Token usage information")
```

---

## 8. Async/Await Best Practices

### 8.1 Use Async for I/O Operations

```python
# ✓ Good: Async for external API calls
async def call_fireworks(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.fireworks.ai/inference/v1/completions",
            json={"prompt": prompt}
        )
        return response.json()

# ✗ Bad: Blocking I/O in async context
async def call_fireworks(prompt: str) -> str:
    response = requests.post(...)  # Blocks! Don't do this
    return response.json()
```

### 8.2 Async Context Managers

```python
# ✓ Good: Use context managers
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=data)

# ✗ Bad: Manual resource management
client = httpx.AsyncClient()
response = await client.post(url, json=data)
# Forgot to close client!
```

---

## 9. Logging Standards

### 9.1 Logger Setup

```python
import logging

# In app/__init__.py or main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# In each module
logger = logging.getLogger(__name__)
```

### 9.2 Log Levels

```python
logger.debug("Detailed information, typically for debugging")
logger.info("Informational messages")
logger.warning("Warning messages for potentially bad situations")
logger.error("Error messages for serious problems")
logger.critical("Critical messages for very serious problems")

# ✓ Good examples
logger.info(f"Classified prompt as: {task_type}")
logger.warning(f"Model timed out after {timeout}s, using fallback")
logger.error(f"All models failed: {error_detail}")
```

### 9.3 Structured Logging

```python
# ✓ Good: Include context
logger.info(
    "Request processed successfully",
    extra={
        "request_id": request_id,
        "task_type": task_type,
        "model": model_name,
        "tokens": tokens_used,
        "latency_ms": latency
    }
)

# ✗ Bad: String concatenation
logger.info(f"Request {request_id} processed by {model_name}")
```

---

## 10. Configuration Management

### 10.1 Use Environment Variables

```python
# app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    debug: bool = False
    fireworks_api_key: str
    ollama_url: str = "http://localhost:11434"
    database_url: str = "sqlite:///./data/metrics.db"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 10.2 Usage

```python
# In main.py
from app.config import settings

app = FastAPI(debug=settings.debug)

# In services
from app.config import settings

api_key = settings.fireworks_api_key
```

---

## 11. Code Review Checklist

Before submitting code for review:

- [ ] Code follows PEP 8 (run `black` and `flake8`)
- [ ] Type hints present (run `mypy`)
- [ ] Tests written and passing (run `pytest`)
- [ ] Docstrings added
- [ ] No hardcoded secrets or credentials
- [ ] No unused imports
- [ ] Error handling implemented
- [ ] Logging added for debugging
- [ ] Comments explain "why", not "what"
- [ ] Function complexity reasonable (cyclomatic complexity < 10)

---

## 12. Common Mistakes to Avoid

### ✗ Using `requests` in async code
```python
# BAD
async def fetch_data():
    return requests.get(url)  # Blocks!

# GOOD
async def fetch_data():
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```

### ✗ Catching all exceptions
```python
# BAD
try:
    result = process()
except:
    pass

# GOOD
try:
    result = process()
except SpecificError as e:
    logger.error(f"Error: {e}")
    raise
```

### ✗ Hardcoding values
```python
# BAD
API_KEY = "sk-1234567890"

# GOOD
API_KEY = os.getenv("FIREWORKS_API_KEY")
```

### ✗ No error messages
```python
# BAD
if not prompt:
    raise ValueError()

# GOOD
if not prompt:
    raise ValueError("Prompt cannot be empty")
```

---

## 13. Tools & Commands

### Run Formatter
```bash
black app/ tests/ --line-length 100
```

### Run Linter
```bash
flake8 app/ tests/ --max-line-length 100
```

### Run Type Checker
```bash
mypy app/
```

### Run All Checks
```bash
black app/ tests/
flake8 app/ tests/
mypy app/
pytest -v --cov=app
```

---

## 14. Pre-Commit Hook (Optional)

**File: `.git/hooks/pre-commit`**
```bash
#!/bin/bash
black app/ tests/
flake8 app/ tests/
mypy app/
pytest -v
if [ $? -ne 0 ]; then
  echo "Tests failed, commit aborted"
  exit 1
fi
```

---

## End of Code Style Guide
