# 🧪 Test Plan & Verification Cases
**Project:** Intelligent Multi-Model Fallback Router  

---

## 1. Testing Scopes
*   **Unit Testing:** Validate each classification tier in [classifier.py](file:///mnt/c/Users/ishar/Projects/AMD/app/services/classifier.py) independently.
*   **Integration Testing:** Verify the complete route process flow (`FastAPI -> TaskClassifier -> ModelExecutor -> SQLite`).
*   **Stress Testing:** Execute rapid, sequential model swaps to verify ROCm memory releases successfully (zero memory leaks).

---

## 2. 10 Verification Cases
These test scenarios evaluate classification correctness, routing paths, and fallback mechanisms:

### Scenario A: Coding Classification (Primary: `kimi-k2p7-code`)
1.  **Test Case 1 (Python Code):**
    *   *Input:* "Write a Python function to compute the Fibonacci sequence using memoization."
    *   *Expected Route:* `ollama:kimi-k2p7-code`
2.  **Test Case 2 (Bug Fix):**
    *   *Input:* "Why do I get a Segmentation Fault in this C++ pointer assignment?"
    *   *Expected Route:* `ollama:kimi-k2p7-code`

### Scenario B: Math Classification (Primary: `gemma-4-31b-it`)
3.  **Test Case 3 (Algebra):**
    *   *Input:* "Find all real solutions for x in the equation log(x) + log(x-3) = 1."
    *   *Expected Route:* `ollama:gemma-4-31b-it`
4.  **Test Case 4 (Calculus):**
    *   *Input:* "Explain how to calculate the derivative of a composite function using the chain rule."
    *   *Expected Route:* `ollama:gemma-4-31b-it`

### Scenario C: Research & Summarization (Primary: `gemma-4-26b-a4b-it`)
5.  **Test Case 5 (Summarization):**
    *   *Input:* "Provide a concise summary of the primary causes of the French Revolution."
    *   *Expected Route:* `ollama:gemma-4-26b-a4b-it`
6.  **Test Case 6 (Explanation):**
    *   *Input:* "What is the difference between nuclear fission and fusion? Explain in detail."
    *   *Expected Route:* `ollama:gemma-4-26b-a4b-it`

### Scenario D: Casual Chat (Primary: `minimax-m3`)
7.  **Test Case 7 (Greetings):**
    *   *Input:* "Hello! Introduce yourself and tell me what you can do."
    *   *Expected Route:* `ollama:minimax-m3`
8.  **Test Case 8 (Humor):**
    *   *Input:* "Tell me a joke about computers or programming."
    *   *Expected Route:* `ollama:minimax-m3`

### Scenario E: Fallback Operations
9.  **Test Case 9 (Primary Load Failure):**
    *   *Input:* "Solve the math problem: calculate the standard deviation of [1, 2, 3, 4, 5]."
    *   *Simulated Action:* Emulate a memory allocation error (`torch.cuda.OutOfMemoryError`) on the primary model `gemma-4-31b-it`.
    *   *Expected Route:* Graceful fallback to `gemma-4-31b-it-nvfp4` (quantized 4-bit) or `gemma-4-26b-a4b-it`.
10. **Test Case 10 (Total Service Outage):**
    *   *Input:* "Write a script to list files in a directory."
    *   *Simulated Action:* Temporarily simulate local Ollama service offline.
    *   *Expected Route:* FastAPI returns an HTTP 500 degraded service JSON response outlining attempts and errors.
