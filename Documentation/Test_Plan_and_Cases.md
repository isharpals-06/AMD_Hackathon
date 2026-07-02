# Test Plan & Test Cases
## Multi-Model Fallback Router

**Version:** 1.0  
**Last Updated:** July 2026  

---

## 1. Test Strategy Overview

### Testing Scope
This document covers:
- **Unit tests:** Individual components (classifier, router, executor)
- **Integration tests:** Component interactions
- **API tests:** HTTP endpoint validation
- **Acceptance tests:** Full end-to-end scenarios (test suite for judges)

### Testing Levels

| Level | Scope | Tools | Coverage |
|-------|-------|-------|----------|
| **Unit** | Classifier, Router, Token counter | pytest | 80%+ |
| **Integration** | Services working together | pytest | 70%+ |
| **API** | HTTP endpoints | pytest + httpx | 90%+ |
| **Acceptance** | Full workflows, judge test suite | Manual | 10 test cases |

### Quality Gates
- Minimum 80% code coverage
- All tests passing before submission
- No critical bugs in acceptance tests
- Reproducible results across environments

---

## 2. Test Data & Fixtures

### Fixture: Sample Prompts

#### Summarization Prompts
```python
SUMMARIZATION_PROMPTS = {
    "article": """
        Climate change is one of the most pressing challenges of our time. 
        Rising global temperatures are causing ice caps to melt, leading to 
        higher sea levels. This threatens coastal cities and ecosystems worldwide. 
        Scientists agree that human activities, particularly greenhouse gas 
        emissions, are the primary cause. Governments are implementing policies 
        to reduce carbon emissions and transition to renewable energy sources. 
        However, the pace of change needs to accelerate to meet climate goals.
    """,
    
    "meeting_notes": """
        Q3 Planning Meeting - July 10, 2026
        Attendees: Alice (PM), Bob (Eng Lead), Carol (Design)
        
        Key Decisions:
        1. Release new dashboard by July 31
        2. Hire 2 engineers before August
        3. Shift focus to mobile optimization
        
        Action Items:
        - Alice: Finalize requirements (due July 15)
        - Bob: Setup CI/CD pipeline (due July 20)
        - Carol: Design mockups (due July 18)
        
        Risks: API integration delays, timeline tight
    """,
    
    "research_abstract": """
        Quantum Computing Applications in Drug Discovery
        
        Abstract: We present a novel approach to accelerating drug discovery 
        using quantum computing algorithms. Traditional methods require 
        simulating molecular behavior on classical computers, which is 
        computationally expensive. Quantum computers can solve these 
        problems exponentially faster. We implemented a quantum-classical 
        hybrid algorithm on IBM Qiskit and achieved 100x speedup for 
        molecular docking simulations compared to classical methods. 
        Results suggest quantum computing could reduce drug discovery 
        timelines from 10 years to under 3 years.
    """
}
```

#### Coding Prompts
```python
CODING_PROMPTS = {
    "simple": "Write a Python function to check if a number is prime",
    
    "medium": """
        Implement a binary search tree in Python with insert, delete, 
        and search operations. Include error handling.
    """,
    
    "complex": """
        Design a concurrent task queue system in Go that:
        - Accepts tasks from multiple producers
        - Processes tasks concurrently
        - Implements backpressure when queue is full
        - Gracefully handles worker failures
        - Provides metrics on throughput and latency
    """
}
```

#### Code Review Prompts
```python
CODE_REVIEW_PROMPTS = {
    "security": """
        Review this Go function for security issues:
        
        func getUserData(userID string, db *sql.DB) (string, error) {
            query := "SELECT email FROM users WHERE id=" + userID
            rows, err := db.Query(query)
            if err != nil {
                return "", err
            }
            // ... rest of code
        }
    """,
    
    "performance": """
        Review this Python code for performance issues:
        
        def find_duplicates(arr):
            result = []
            for i in range(len(arr)):
                for j in range(i+1, len(arr)):
                    if arr[i] == arr[j]:
                        result.append(arr[i])
            return list(set(result))
    """,
    
    "style": """
        Review this JavaScript code for best practices:
        
        function processData(data) {
            var result = [];
            for(var i=0; i<data.length; i++) {
                var item = data[i];
                if(item.active == true) {
                    var processed = item.value * 2;
                    result.push(processed);
                }
            }
            return result;
        }
    """
}
```

---

## 3. Unit Tests

### 3.1 Classifier Tests

```python
# tests/test_classifier.py
import pytest
from app.services.classifier import TaskClassifier

@pytest.fixture
def classifier():
    return TaskClassifier()

class TestClassifier:
    
    def test_classify_summarization_basic(self, classifier):
        """Test basic summarization classification"""
        prompt = "Summarize this article about quantum computing"
        result = classifier.classify(prompt)
        assert result == "summarization"
    
    def test_classify_summarization_variations(self, classifier):
        """Test various summarization keywords"""
        prompts = [
            "Give me a summary of the following text",
            "Can you summarize the main points",
            "Write a summary of this paper",
            "Condense this into a brief summary"
        ]
        for prompt in prompts:
            result = classifier.classify(prompt)
            assert result == "summarization", f"Failed for: {prompt}"
    
    def test_classify_coding(self, classifier):
        """Test coding classification"""
        prompts = [
            "Write a Python function to sort an array",
            "Implement a binary search tree",
            "Code a solution to this problem",
            "Generate a REST API in Go"
        ]
        for prompt in prompts:
            result = classifier.classify(prompt)
            assert result == "coding", f"Failed for: {prompt}"
    
    def test_classify_code_review(self, classifier):
        """Test code review classification"""
        prompts = [
            "Review this code for security issues",
            "Check this function for bugs",
            "Code review: find any problems",
            "Analyze this code for performance"
        ]
        for prompt in prompts:
            result = classifier.classify(prompt)
            assert result == "code_review", f"Failed for: {prompt}"
    
    def test_classify_edge_case_multiple_keywords(self, classifier):
        """Test when prompt has multiple task keywords"""
        # "Review" and "code" appear - code_review takes priority if both present
        prompt = "Review this Python code for issues"
        result = classifier.classify(prompt)
        # Define priority: code_review > coding > summarization
        assert result in ["code_review", "coding"]
    
    def test_classify_general_fallback(self, classifier):
        """Test fallback to general when no keyword match"""
        prompt = "Tell me about history of Rome"
        result = classifier.classify(prompt)
        assert result == "general"
    
    def test_classify_case_insensitive(self, classifier):
        """Test classification is case-insensitive"""
        prompts = [
            "SUMMARIZE this article",
            "Write CODE for this",
            "REVIEW this code"
        ]
        results = [classifier.classify(p) for p in prompts]
        assert results[0] == "summarization"
        assert results[1] == "coding"
        assert results[2] == "code_review"

    def test_classify_vector_db_fallback(self, classifier):
        """Test fallback to regex if Vector DB query fails"""
        # Force fallback to test regex path directly
        result = classifier.classify("Write a python function to sort an array", force_fallback=True)
        assert result == "coding"
```

### 3.2 Router Tests

```python
# tests/test_router.py
import pytest
from app.services.router import RoutingEngine

@pytest.fixture
def router():
    return RoutingEngine()

class TestRouter:
    
    def test_route_summarization_to_ollama(self, router):
        """Test summarization routes to local Ollama"""
        routing = router.get_routing("summarization")
        assert routing["primary_model"] == "ollama:qwen"
        assert routing["timeout_seconds"] == 10
    
    def test_route_coding_to_mixtral(self, router):
        """Test coding routes to Fireworks Mixtral"""
        routing = router.get_routing("coding")
        assert routing["primary_model"] == "fireworks:mixtral"
        assert routing["fallback_model"] == "fireworks:qwen-72b"
    
    def test_route_code_review_to_mixtral(self, router):
        """Test code review routes to Mixtral"""
        routing = router.get_routing("code_review")
        assert routing["primary_model"] == "fireworks:mixtral"
    
    def test_route_general_to_mixtral(self, router):
        """Test general tasks default to Mixtral"""
        routing = router.get_routing("general")
        assert routing["primary_model"] == "fireworks:mixtral"
    
    def test_route_has_fallback(self, router):
        """Test all routes have fallback model"""
        for task_type in ["summarization", "coding", "code_review"]:
            routing = router.get_routing(task_type)
            assert "fallback_model" in routing
            assert routing["fallback_model"] is not None
    
    def test_route_has_retry_config(self, router):
        """Test all routes have retry configuration"""
        for task_type in ["summarization", "coding"]:
            routing = router.get_routing(task_type)
            assert "max_retries" in routing
            assert routing["max_retries"] >= 1
```

### 3.3 Token Counter Tests

```python
# tests/test_token_counter.py
import pytest
from app.services.token_counter import TokenCounter

@pytest.fixture
def counter():
    return TokenCounter()

class TestTokenCounter:
    
    def test_estimate_tokens_short(self, counter):
        """Test token estimation for short text"""
        text = "Hello world"
        tokens = counter.estimate_tokens(text)
        assert 1 <= tokens <= 5  # Rough estimate
    
    def test_estimate_tokens_medium(self, counter):
        """Test token estimation for medium text"""
        text = "This is a longer piece of text that should estimate to a reasonable number of tokens."
        tokens = counter.estimate_tokens(text)
        assert 10 <= tokens <= 30
    
    def test_estimate_tokens_consistency(self, counter):
        """Test same text produces same token count"""
        text = "Consistent token counting test"
        tokens1 = counter.estimate_tokens(text)
        tokens2 = counter.estimate_tokens(text)
        assert tokens1 == tokens2
    
    def test_calculate_cost_ollama(self, counter):
        """Test cost calculation for Ollama (free)"""
        cost = counter.calculate_cost(model="ollama:qwen", tokens=1000)
        assert cost == 0.0
    
    def test_calculate_cost_mixtral(self, counter):
        """Test cost calculation for Fireworks Mixtral"""
        # Mixtral: $0.0005 per 1k input, $0.0015 per 1k output
        cost = counter.calculate_cost(
            model="fireworks:mixtral",
            input_tokens=1000,
            output_tokens=500
        )
        expected = (1000 * 0.0005 / 1000) + (500 * 0.0015 / 1000)
        assert abs(cost - expected) < 0.00001
```

---

## 4. Integration Tests

```python
# tests/test_integration.py
import pytest
from app.services.classifier import TaskClassifier
from app.services.router import RoutingEngine

class TestIntegration:
    
    def test_classify_and_route_summarization(self):
        """Test classification and routing workflow"""
        classifier = TaskClassifier()
        router = RoutingEngine()
        
        prompt = "Summarize this article"
        task_type = classifier.classify(prompt)
        routing = router.get_routing(task_type)
        
        assert task_type == "summarization"
        assert routing["primary_model"] == "ollama:qwen"
    
    def test_classify_and_route_coding(self):
        """Test classification and routing for coding"""
        classifier = TaskClassifier()
        router = RoutingEngine()
        
        prompt = "Write a Python function to sort numbers"
        task_type = classifier.classify(prompt)
        routing = router.get_routing(task_type)
        
        assert task_type == "coding"
        assert routing["primary_model"] == "fireworks:mixtral"
```

---

## 5. API Tests

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestAPI:
    
    def test_post_process_success(self, client):
        """Test successful request processing"""
        response = client.post("/process", json={
            "prompt": "Summarize quantum computing",
            "task_type": "summarization"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "result" in data
        assert "tokens" in data
    
    def test_post_process_validation_error(self, client):
        """Test validation error for short prompt"""
        response = client.post("/process", json={
            "prompt": "Short"  # Too short
        })
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_post_process_auto_classify(self, client):
        """Test auto-classification when task_type not provided"""
        response = client.post("/process", json={
            "prompt": "Write a Python function for binary search"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["task_type"] == "coding"
    
    def test_get_health(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
    
    def test_get_metrics(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "aggregated_metrics" in data
        assert "total_requests" in data["aggregated_metrics"]
```

---

## 6. Acceptance Test Cases (For Judges)

### Overview
These 10 test cases are used to evaluate token efficiency and accuracy.

### Baseline Calculation
**Assumption:** Using only Fireworks Mixtral for all requests
```
Expected total tokens: ~5,400
Expected cost: ~$0.008
Success rate: 85%
```

### Test Suite

#### TEST 1: Summarization - News Article
```
Input:
  Prompt: "Summarize this news article: [500-word article about AI regulation]"
  Task Type: "summarization"
  
Expected Behavior:
  - Classified as: summarization ✓
  - Routed to: Ollama (Qwen 7B) ✓
  - Should succeed in: <5 seconds
  - Token estimate: 150-200 tokens
  
Success Criteria:
  ✓ Summary captures main points
  ✓ ~200 words output
  ✓ Latency < 5 seconds
  ✓ Tokens < 250 (savings vs Mixtral's ~350)
```

#### TEST 2: Summarization - Technical Paper Abstract
```
Input:
  Prompt: "Summarize this ML research abstract: [technical abstract]"
  Task Type: "summarization"
  
Expected Behavior:
  - Routed to: Ollama
  - Token estimate: 180-250 tokens
  
Success Criteria:
  ✓ Technically accurate summary
  ✓ Preserves key contributions
  ✓ Tokens < 300
```

#### TEST 3: Summarization - Meeting Notes
```
Input:
  Prompt: "Summarize these meeting notes: [meeting notes]"
  Task Type: "summarization"
  
Expected Behavior:
  - Routed to: Ollama
  - Token estimate: 120-180 tokens
  
Success Criteria:
  ✓ Captures action items
  ✓ Lists decisions and owners
  ✓ Tokens < 220
```

#### TEST 4: Coding - Simple Function
```
Input:
  Prompt: "Write a Python function to check if a number is prime"
  Task Type: "coding"
  
Expected Behavior:
  - Classified as: coding ✓
  - Routed to: Fireworks Mixtral ✓
  - Token estimate: 400-500 tokens
  
Success Criteria:
  ✓ Code is syntactically correct
  ✓ Handles edge cases (1, 2, negative numbers)
  ✓ Efficient algorithm (not brute force)
  ✓ Well-commented
  ✓ Tokens: 400-550
```

#### TEST 5: Coding - Complex Algorithm
```
Input:
  Prompt: "Implement a concurrent task queue in Go with backpressure"
  Task Type: "coding"
  
Expected Behavior:
  - Routed to: Fireworks Mixtral
  - Token estimate: 800-1000 tokens
  
Success Criteria:
  ✓ Uses Go concurrency patterns (goroutines, channels)
  ✓ Implements backpressure
  ✓ Has error handling
  ✓ Production-quality code
```

#### TEST 6: Coding - Refactoring
```
Input:
  Prompt: "Refactor this JavaScript code for performance: [code]"
  Task Type: "coding"
  
Expected Behavior:
  - Routed to: Fireworks Mixtral
  - Token estimate: 550-700 tokens
  
Success Criteria:
  ✓ Improved efficiency
  ✓ Cleaner code structure
  ✓ Better variable names
```

#### TEST 7: Code Review - Security Issues
```
Input:
  Prompt: "Review this Go code for security vulnerabilities: [SQL injection code]"
  Task Type: "code_review"
  
Expected Behavior:
  - Classified as: code_review ✓
  - Routed to: Fireworks Mixtral ✓
  - Token estimate: 450-600 tokens
  
Success Criteria:
  ✓ Identifies SQL injection vulnerability
  ✓ Explains the risk
  ✓ Suggests parameterized queries fix
  ✓ Provides corrected code
```

#### TEST 8: Code Review - Performance Issues
```
Input:
  Prompt: "Review this database query for performance: [inefficient SQL]"
  Task Type: "code_review"
  
Expected Behavior:
  - Routed to: Fireworks Mixtral
  - Token estimate: 400-550 tokens
  
Success Criteria:
  ✓ Identifies missing indexes
  ✓ Suggests query optimization
  ✓ Explains performance impact
```

#### TEST 9: Code Review - Style & Best Practices
```
Input:
  Prompt: "Review this Python code for best practices: [code]"
  Task Type: "code_review"
  
Expected Behavior:
  - Routed to: Fireworks Mixtral
  - Token estimate: 500-650 tokens
  
Success Criteria:
  ✓ Identifies style issues
  ✓ Suggests PEP 8 improvements
  ✓ Recommends better patterns
```

#### TEST 10: Edge Case - Fallback on Timeout
```
Input:
  Prompt: "Generate a complex sorting algorithm in Rust"
  Expected Timeout: Primary model times out after 10 seconds
  
Expected Behavior:
  - Try Mixtral (times out)
  - Fallback to Qwen-72B
  - Qwen-72B succeeds
  - Result returned with "success_via_fallback" status
  
Success Criteria:
  ✓ No error shown to user
  ✓ Fallback model succeeds
  ✓ Result quality acceptable
  ✓ Total latency < 30 seconds
  ✓ Log shows fallback event
```

---

## 7. Test Execution Plan

### Pre-Submission Testing (Day 5)

```
Morning (Sunrise to 9 AM):
  1. Run all unit tests
  2. Run all integration tests
  3. Run all API tests
  4. Fix any failures

Mid-Morning (9 AM to 12 PM):
  5. Manually execute acceptance test cases (TEST 1-10)
  6. Record results and token counts
  7. Calculate total tokens vs baseline
  8. Verify token savings >= 25%

Afternoon (12 PM to 3 PM):
  9. Create metrics summary
  10. Document any failures
  11. Final health check
  12. Package submission

Late Afternoon (3 PM - Submission):
  13. Final review
  14. Upload to lablab.ai
```

### Test Results Recording

```
Test: TEST 1 - Summarization News Article
Date: 2026-07-11
Status: PASS ✓
Metrics:
  - Input tokens: 520
  - Output tokens: 125
  - Total tokens: 645
  - Expected baseline (Mixtral): 850
  - Savings: 24% ✓
  - Latency: 2.3 seconds
  - Accuracy: ✓ (all main points captured)
```

---

## 8. CI/CD Integration

### GitHub Actions (Optional for Hackathon)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - run: pip install -r requirements.txt
      - run: pytest -v --cov=app
```

---

## 9. Known Issues & Limitations

### Current Limitations
1. **No authentication:** Anyone can call the API (fine for hackathon)
2. **Single-instance only:** No load balancing implemented
3. **SQLite:** Not suitable for high-concurrency production
4. **No caching:** Same prompt processed twice = double tokens

### Test Limitations
1. **API-based testing:** Depends on external service availability
2. **Timing-based tests:** May fail on slow systems
3. **Ollama requirement:** Tests fail if Ollama not running

---

## End of Test Plan
