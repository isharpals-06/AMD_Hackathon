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
OLLAMA_ROUTER_MODEL = os.getenv("OLLAMA_ROUTER_MODEL", "llama3-router")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "10.0"))

# ChromaDB settings (kept for reference, but disabled)
CHROMADB_DIR = os.getenv("CHROMADB_DIR", "./data/chromadb")

# Fireworks settings
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "")
FIREWORKS_TIMEOUT = float(os.getenv("FIREWORKS_TIMEOUT", "15.0"))

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/metrics.db")

# HuggingFace token
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Model Mapping Overrides (Dynamic Local 8GB GPU vs Cloud scaling)
MATH_PRIMARY_MODEL = os.getenv("MATH_PRIMARY_MODEL", "huggingface:Qwen/Qwen2.5-Math-7B-Instruct")
MATH_FALLBACK_MODEL = os.getenv("MATH_FALLBACK_MODEL", "huggingface:meta-llama/Llama-3.1-8B-Instruct")

CODING_PRIMARY_MODEL = os.getenv("CODING_PRIMARY_MODEL", "huggingface:Qwen/Qwen2.5-Coder-32B-Instruct")
CODING_FALLBACK_MODEL = os.getenv("CODING_FALLBACK_MODEL", "huggingface:Qwen/Qwen2.5-Coder-7B-Instruct")

RESEARCH_PRIMARY_MODEL = os.getenv("RESEARCH_PRIMARY_MODEL", "huggingface:meta-llama/Llama-3.1-8B-Instruct")
RESEARCH_FALLBACK_MODEL = os.getenv("RESEARCH_FALLBACK_MODEL", "huggingface:microsoft/Phi-3-mini-4k-instruct")

CASUAL_PRIMARY_MODEL = os.getenv("CASUAL_PRIMARY_MODEL", "huggingface:microsoft/Phi-3-mini-4k-instruct")
CASUAL_FALLBACK_MODEL = os.getenv("CASUAL_FALLBACK_MODEL", "huggingface:Qwen/Qwen2.5-7B-Instruct")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
