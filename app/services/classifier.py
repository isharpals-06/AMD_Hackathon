import logging
import json
import re
from app.services.ollama_client import OllamaClient
from app import config

logger = logging.getLogger(__name__)

# Try to import chromadb. If not installed, we fallback gracefully.
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb library not available. TaskClassifier will run in SLM + Regex mode.")

class TaskClassifier:
    def __init__(self, persist_directory: str = "./data/chromadb"):
        self.chroma_client = None
        self.collection = None
        self.persist_directory = persist_directory
        
        if CHROMADB_AVAILABLE:
            try:
                # Initialize local ChromaDB client for vector lookup fallback
                self.chroma_client = chromadb.PersistentClient(path=persist_directory)
                self.collection = self.chroma_client.get_or_create_collection(name="routing_seed_prompts")
                self._seed_database_if_empty()
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}.")

    def _seed_database_if_empty(self):
        """Pre-populates ChromaDB with seed examples for vector fallback."""
        if self.collection.count() == 0:
            logger.info("Seeding ChromaDB with category examples...")
            seed_data = [
                # Math Tasks
                ("Solve for x: 3x + 5 = 20", "math"),
                ("What is the derivative of sin(x) * cos(x)?", "math"),
                ("Calculate the integral of x^2 from 0 to 5.", "math"),
                ("Prove that the square root of 2 is irrational.", "math"),
                
                # Coding Tasks
                ("Write a Python function to sort a list using quicksort.", "coding"),
                ("Implement a binary search tree in C++.", "coding"),
                ("How do I fix a NullPointerException in Java?", "coding"),
                
                # Research Tasks
                ("Summarize the main events of World War II.", "research"),
                ("Explain the concept of quantum computing in detail.", "research"),
                ("What are the primary causes of global inflation in 2026?", "research"),
                
                # Casual Chat Tasks
                ("Hello! How are you doing today?", "casual_chat"),
                ("Tell me a funny joke about programming.", "casual_chat"),
                ("Who are you, and what can you do?", "casual_chat")
            ]
            for i, (text, category) in enumerate(seed_data):
                self.collection.add(
                    documents=[text],
                    metadatas=[{"category": category}],
                    ids=[f"seed_{category}_{i}"]
                )

    def classify_regex(self, prompt: str) -> str:
        """Tier 3: Regex-based keyword classification fallback."""
        prompt_lower = prompt.lower()
        if any(kw in prompt_lower for kw in ["solve", "calculate", "derivative", "integral", "equation", "matrix", "math", "sum of"]):
            return "math"
        if any(kw in prompt_lower for kw in ["write a function", "implement", "debug", "code", "class ", "def ", "function", "javascript", "python", "c++", "rust"]):
            return "coding"
        if any(kw in prompt_lower for kw in ["summarize", "research", "explain", "compare", "contrast", "history of", "latest news", "abstract"]):
            return "research"
        return "casual_chat"

    async def classify_chromadb(self, prompt: str) -> str:
        """Tier 2: ChromaDB Vector search classification fallback."""
        if not CHROMADB_AVAILABLE or not self.collection:
            raise ValueError("ChromaDB is not initialized.")
            
        # 1. Generate embedding using Ollama nomic-embed-text
        embedding = await OllamaClient.get_embedding(prompt)
        if not embedding:
            raise ValueError("Empty embedding returned from Ollama")
            
        # 2. Query ChromaDB for closest match
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=3
        )
        
        # 3. Extract matching categories
        metadatas = results.get("metadatas", [[]])[0]
        categories = [m.get("category") for m in metadatas if m]
        if not categories:
            raise ValueError("No matching categories found in ChromaDB query")
            
        # 4. Return majority class
        return max(set(categories), key=categories.count)

    async def classify(self, prompt: str, force_fallback: bool = False) -> dict:
        """
        Classifies prompt using 3 progressive fallback tiers:
        Tier 1: Fine-Tuned SLM (Llama 3.2 1B QLoRA)
        Tier 2: Vector Search (ChromaDB + nomic-embed-text)
        Tier 3: Keywords (Regex rules)
        """
        # Pre-check Ollama health to prevent long connection timeouts (default: 30s)
        ollama_active = await OllamaClient.check_health()
        
        if not ollama_active:
            logger.info("Ollama server is offline. Bypassing Tiers 1 & 2 to prevent timeout hangs.")
            category = self.classify_regex(prompt)
            # Default model mapping for category
            primary = config.CASUAL_PRIMARY_MODEL
            if category == "coding":
                primary = config.CODING_PRIMARY_MODEL
            elif category == "math":
                primary = config.MATH_PRIMARY_MODEL
            elif category == "research":
                primary = config.RESEARCH_PRIMARY_MODEL
                
            return {
                "category": category,
                "primary_model": primary,
                "fallback_model": config.CASUAL_FALLBACK_MODEL
            }

        if force_fallback:
            logger.info("Forcing fallback routing.")
            category = self.classify_regex(prompt)
            return {"category": category, "primary_model": config.MATH_PRIMARY_MODEL, "fallback_model": config.MATH_FALLBACK_MODEL}

        # --- TIER 1: Fine-Tuned SLM ---
        try:
            logger.info(f"Tier 1: Querying local SLM router: {config.OLLAMA_ROUTER_MODEL}")
            instruction_prompt = f"""### Instruction:
You are an intelligent AI model router.

Analyze the user's request and decide:
1. Task category
2. Best model to handle the request
3. Backup model if the first model fails

Return only JSON output.

### User Request:
{prompt}

### Response:
"""
            result = await OllamaClient.generate(instruction_prompt, model=config.OLLAMA_ROUTER_MODEL)
            output_text = result.get("text", "").strip()
            
            # Robust JSON extraction from LLM output
            import re
            json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group(0))
            else:
                decision = json.loads(output_text)
                
            logger.info(f"Tier 1 SLM routing decision succeeded: {decision}")
            category = decision.get("task_type") or decision.get("category") or "casual_chat"
            
            # Map category to configured cloud Hugging Face models as requested
            primary = config.CASUAL_PRIMARY_MODEL
            fallback = config.CASUAL_FALLBACK_MODEL
            
            if category == "coding":
                primary = config.CODING_PRIMARY_MODEL
                fallback = config.CODING_FALLBACK_MODEL
            elif category == "math":
                primary = config.MATH_PRIMARY_MODEL
                fallback = config.MATH_FALLBACK_MODEL
            elif category == "research":
                primary = config.RESEARCH_PRIMARY_MODEL
                fallback = config.RESEARCH_FALLBACK_MODEL
                
            return {
                "category": category,
                "primary_model": primary,
                "fallback_model": fallback
            }
        except Exception as slm_err:
            logger.warning(f"Tier 1 SLM router failed: {slm_err}. Switching to Tier 2 (ChromaDB).")

        # --- TIER 2: ChromaDB Vector Match ---
        try:
            category = await self.classify_chromadb(prompt)
            logger.info(f"Tier 2 ChromaDB classification succeeded: '{category}'")
            
            # Default model mapping for category
            primary = config.CASUAL_PRIMARY_MODEL
            if category == "coding":
                primary = config.CODING_PRIMARY_MODEL
            elif category == "math":
                primary = config.MATH_PRIMARY_MODEL
            elif category == "research":
                primary = config.RESEARCH_PRIMARY_MODEL
                
            return {
                "category": category,
                "primary_model": primary,
                "fallback_model": config.CASUAL_FALLBACK_MODEL
            }
        except Exception as chroma_err:
            logger.warning(f"Tier 2 ChromaDB failed: {chroma_err}. Switching to Tier 3 (Regex).")

        # --- TIER 3: Regex Fallback ---
        category = self.classify_regex(prompt)
        logger.info(f"Tier 3 Regex classification succeeded: '{category}'")
        primary = config.CASUAL_PRIMARY_MODEL
        if category == "coding":
            primary = config.CODING_PRIMARY_MODEL
        elif category == "math":
            primary = config.MATH_PRIMARY_MODEL
        elif category == "research":
            primary = config.RESEARCH_PRIMARY_MODEL
            
        return {
            "category": category,
            "primary_model": primary,
            "fallback_model": config.CASUAL_FALLBACK_MODEL
        }


