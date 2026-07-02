import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

DEBUG = os.getenv("DEBUG", "True").lower() == "true"
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen:7b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "10.0"))

# ChromaDB settings
CHROMADB_DIR = os.getenv("CHROMADB_DIR", "./data/chromadb")

# Fireworks settings
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "")
FIREWORKS_TIMEOUT = float(os.getenv("FIREWORKS_TIMEOUT", "15.0"))

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/metrics.db")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
