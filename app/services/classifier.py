import logging
import re
from app.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

# Try to import chromadb. If not installed, we fallback gracefully to regex.
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb library not available. TaskClassifier will run in regex-only mode.")

class TaskClassifier:
    def __init__(self, persist_directory: str = "./data/chromadb"):
        self.chroma_client = None
        self.collection = None
        self.persist_directory = persist_directory
        
        if CHROMADB_AVAILABLE:
            try:
                # Initialize local ChromaDB client (in-memory or persistent)
                self.chroma_client = chromadb.PersistentClient(path=persist_directory)
                self.collection = self.chroma_client.get_or_create_collection(name="routing_seed_prompts")
                self._seed_database_if_empty()
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}. Falling back to Regex.")

    def _seed_database_if_empty(self):
        """Pre-populates the vector DB with seed examples if empty."""
        if self.collection.count() == 0:
            logger.info("Seeding ChromaDB with category examples...")
            
            # Example prompts mapping to categories
            seed_data = [
                # Math Tasks
                ("Solve for x: 3x + 5 = 20", "math"),
                ("What is the derivative of sin(x) * cos(x)?", "math"),
                ("Calculate the integral of x^2 from 0 to 5.", "math"),
                ("Prove that the square root of 2 is irrational.", "math"),
                ("Find the eigenvalues of the following matrix.", "math"),
                
                # Coding Tasks
                ("Write a Python function to sort a list using quicksort.", "coding"),
                ("Implement a binary search tree in C++.", "coding"),
                ("How do I fix a NullPointerException in Java?", "coding"),
                ("Create a REST API endpoint in Go using Gin.", "coding"),
                ("Generate a CSS stylesheet for a dark mode layout.", "coding"),
                
                # Research / RAG Tasks
                ("Summarize the main events of World War II.", "research"),
                ("Explain the concept of quantum computing in detail.", "research"),
                ("Search for the latest news on AI safety regulation.", "research"),
                ("What are the primary causes of global inflation in 2026?", "research"),
                ("Compare and contrast photosynthesis and cellular respiration.", "research"),
                
                # Casual Chat Tasks
                ("Hello! How are you doing today?", "casual_chat"),
                ("Tell me a funny joke about programming.", "casual_chat"),
                ("What is your favorite book and why?", "casual_chat"),
                ("Hey, let's chat about gaming.", "casual_chat"),
                ("Who are you, and what can you do?", "casual_chat")
            ]
            
            # For seeding in a hackathon context, we can add mock embeddings or generate them.
            # In a real environment, we'd query Ollama for embeddings.
            # To avoid blocker dependencies on Day 1, we seed with dummy vectors
            # and generate actual embeddings dynamically when classification runs.
            # Here we just insert the texts and metadata. ChromaDB allows adding text with metadata.
            # We can use ChromaDB's default embedding function or add documents directly.
            for i, (text, category) in enumerate(seed_data):
                self.collection.add(
                    documents=[text],
                    metadatas=[{"category": category}],
                    ids=[f"seed_{category}_{i}"]
                )

    def classify_regex(self, prompt: str) -> str:
        """Regex-based keyword classification fallback."""
        prompt_lower = prompt.lower()
        
        # Math detection
        if any(kw in prompt_lower for kw in ["solve", "calculate", "derivative", "integral", "equation", "matrix", "math", "sum of"]):
            return "math"
            
        # Code review / Coding detection
        if any(kw in prompt_lower for kw in ["write a function", "implement", "debug", "code", "class ", "def ", "function", "javascript", "python", "c++", "rust"]):
            return "coding"
            
        # Research / RAG detection
        if any(kw in prompt_lower for kw in ["summarize", "research", "explain", "compare", "contrast", "history of", "latest news", "abstract"]):
            return "research"
            
        # Default fallback
        return "casual_chat"

    async def classify(self, prompt: str, force_fallback: bool = False) -> str:
        """Classifies the prompt into 'math', 'coding', 'research', or 'casual_chat'."""
        if force_fallback or not CHROMADB_AVAILABLE or not self.collection:
            logger.info("Running regex-based classification fallback.")
            return self.classify_regex(prompt)
            
        try:
            # 1. Generate embedding using Ollama nomic-embed-text
            embedding = await OllamaClient.get_embedding(prompt)
            if not embedding:
                raise ValueError("Empty embedding returned from Ollama")
                
            # 2. Query ChromaDB for the closest vector
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=3
            )
            
            # 3. Extract matching categories
            metadatas = results.get("metadatas", [[]])[0]
            categories = [m.get("category") for m in metadatas if m]
            
            if not categories:
                raise ValueError("No matching categories found in ChromaDB query")
                
            # 4. Perform majority voting
            majority_class = max(set(categories), key=categories.count)
            logger.info(f"Vector DB classified prompt as: {majority_class} (K-NN matches: {categories})")
            return majority_class
            
        except Exception as e:
            logger.error(f"Error in Vector DB classification: {e}. Falling back to Regex.")
            return self.classify_regex(prompt)
