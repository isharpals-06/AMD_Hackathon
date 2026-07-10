import json
import logging
import re

from app import config
from app.services.ollama_client import OllamaClient

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
                if persist_directory == ":memory:":
                    self.chroma_client = chromadb.EphemeralClient()
                else:
                    self.chroma_client = chromadb.PersistentClient(path=persist_directory)
                self.collection = self.chroma_client.get_or_create_collection(
                    name="routing_seed_prompts"
                )
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
                ("Who are you, and what can you do?", "casual_chat"),
            ]
            for i, (text, category) in enumerate(seed_data):
                self.collection.add(
                    documents=[text],
                    metadatas=[{"category": category}],
                    ids=[f"seed_{category}_{i}"],
                )

    def add_seeds(self, seed_data: list[tuple[str, str]]):
        """Dynamically adds labeled examples to ChromaDB for vector fallback."""
        if not CHROMADB_AVAILABLE or not self.collection:
            raise ValueError("ChromaDB is not initialized.")

        import uuid

        for text, category in seed_data:
            seed_id = f"seed_{category}_{uuid.uuid4().hex[:8]}"
            self.collection.add(documents=[text], metadatas=[{"category": category}], ids=[seed_id])
        logger.info(f"Added {len(seed_data)} seed examples to ChromaDB.")

    def classify_regex(self, prompt: str) -> str:
        """Tier 3: Regex-based keyword classification fallback."""
        prompt_lower = prompt.lower()

        # Word-boundary check helper for short keywords to prevent false positives (like 'api' in 'capitalism')
        def has_word(word: str) -> bool:
            if len(word) <= 4 or word in ["rust", "code", "sql", "api"]:
                return bool(re.search(r"\b" + re.escape(word) + r"\b", prompt_lower))
            return word in prompt_lower

        if any(
            has_word(kw)
            for kw in [
                "solve",
                "calculate",
                "derivative",
                "integral",
                "equation",
                "matrix",
                "math",
                "sum of",
                "eigenvalue",
                "eigenvalues",
                "factorial",
                "polynomial",
            ]
        ):
            return "math"
        if any(
            has_word(kw)
            for kw in [
                "write a function",
                "implement",
                "debug",
                "code",
                "class ",
                "def ",
                "function",
                "javascript",
                "python",
                "c++",
                "rust",
                "api",
                "endpoint",
                "rest api",
                "fastapi",
                "flask",
                "django",
                "create a",
                "program",
                "algorithm",
                "sql",
                "database",
            ]
        ):
            return "coding"
        if any(
            has_word(kw)
            for kw in [
                "summarize",
                "research",
                "explain",
                "compare",
                "contrast",
                "history of",
                "latest news",
                "abstract",
                "causes of",
                "effects of",
            ]
        ):
            return "research"
        return "casual_chat"

    async def classify_chromadb(self, prompt: str) -> str:
        """Tier 2: ChromaDB Vector search classification fallback."""
        if not CHROMADB_AVAILABLE or not self.collection:
            raise ValueError("ChromaDB is not initialized.")

        # Query ChromaDB using text directly — ChromaDB handles local embedding generation automatically
        results = self.collection.query(query_texts=[prompt], n_results=3)

        # Extract matching categories
        metadatas = results.get("metadatas", [[]])[0]
        categories = [m.get("category") for m in metadatas if m]
        if not categories:
            raise ValueError("No matching categories found in ChromaDB query")

        # Return majority class
        return max(set(categories), key=categories.count)

    async def classify(self, prompt: str, force_fallback: bool = False) -> dict:
        """
        Classifies prompt using 3 progressive fallback tiers:
        Tier 1: Fine-Tuned SLM (Llama 3.2 1B QLoRA)
        Tier 2: Vector Search (ChromaDB + nomic-embed-text)
        Tier 3: Keywords (Regex rules)
        """
        if force_fallback:
            logger.info("Forcing fallback routing.")
            category = self.classify_regex(prompt)
            return {
                "category": category,
                "primary_model": "ollama:gemma-4-31b-it",
                "fallback_model": "ollama:gemma-4-26b-a4b-it",
            }

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
            result = await OllamaClient.generate(
                instruction_prompt, model=config.OLLAMA_ROUTER_MODEL
            )
            output_text = result.get("text", "").strip()

            # Robust JSON extraction to handle model prefixes like "assistant\n\n"
            json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
            if json_match:
                output_text = json_match.group(0)

            try:
                decision = json.loads(output_text)
            except Exception:
                import ast

                decision = ast.literal_eval(output_text)

            logger.info(f"Tier 1 SLM routing decision succeeded: {decision}")

            raw_category = (
                (decision.get("task_type") or decision.get("task_category") or "casual_chat")
                .lower()
                .strip()
            )
            if "prog" in raw_category or "cod" in raw_category:
                category = "coding"
            elif "math" in raw_category:
                category = "math"
            elif "research" in raw_category or "q&a" in raw_category or "qa" in raw_category:
                category = "research"
            else:
                category = "casual_chat"

            from app.services.router import RoutingEngine

            rules = RoutingEngine.get_routing(category)

            return {
                "category": category,
                "primary_model": rules.get("primary_model"),
                "fallback_model": rules.get("fallback_model"),
            }
        except Exception as slm_err:
            logger.warning(f"Tier 1 SLM router failed: {slm_err}. Switching to Tier 2 (ChromaDB).")

        # --- TIER 2: ChromaDB Vector Match ---
        try:
            category = await self.classify_chromadb(prompt)
            logger.info(f"Tier 2 ChromaDB classification succeeded: '{category}'")

            from app.services.router import RoutingEngine

            rules = RoutingEngine.get_routing(category)

            return {
                "category": category,
                "primary_model": rules.get("primary_model"),
                "fallback_model": rules.get("fallback_model"),
            }
        except Exception as chroma_err:
            logger.warning(f"Tier 2 ChromaDB failed: {chroma_err}. Switching to Tier 3 (Regex).")

        # --- TIER 3: Regex Fallback ---
        category = self.classify_regex(prompt)
        logger.info(f"Tier 3 Regex classification succeeded: '{category}'")

        from app.services.router import RoutingEngine

        rules = RoutingEngine.get_routing(category)

        return {
            "category": category,
            "primary_model": rules.get("primary_model"),
            "fallback_model": rules.get("fallback_model"),
        }
