"""
Application configuration using Pydantic Settings for type-safe, validated config.

All settings are loaded from environment variables or a .env file.
Required secrets (FIREWORKS_API_KEY) are validated at startup.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with full type validation and defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── API Server ────────────────────────────────────────────────────────────
    debug: bool = Field(default=False, description="Enable debug mode (verbose output)")
    port: int = Field(default=8000, ge=1, le=65535, description="API server port")
    host: str = Field(default="0.0.0.0", description="API server host binding")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging verbosity level"
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: list[str] = Field(
        default=["http://localhost", "http://localhost:5173", "http://localhost:80"],
        description="Allowed CORS origins (comma-separated in env)",
    )

    # ── Rate Limiting ────────────────────────────────────────────────────────
    rate_limit_enabled: bool = Field(default=True, description="Enable request rate limiting")
    rate_limit_per_minute: int = Field(
        default=30, ge=1, le=1000, description="Max requests per minute per IP"
    )

    # ── API Key Auth ─────────────────────────────────────────────────────────
    api_key_enabled: bool = Field(default=False, description="Enable API key authentication")
    api_key: str = Field(default="", description="Static API key (leave empty to disable)")

    # ── Ollama ───────────────────────────────────────────────────────────────
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model: str = Field(default="qwen:7b", description="Default Ollama chat model")
    ollama_embed_model: str = Field(
        default="nomic-embed-text", description="Ollama embedding model for ChromaDB"
    )
    ollama_router_model: str = Field(
        default="llama3-router", description="Fine-tuned Llama router model name in Ollama"
    )
    ollama_timeout: float = Field(
        default=60.0, ge=1.0, le=300.0, description="Ollama request timeout (seconds)"
    )

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chromadb_dir: str = Field(
        default="./data/chromadb", description="ChromaDB persistence directory"
    )

    # ── Fireworks Cloud API ───────────────────────────────────────────────────
    fireworks_api_key: str = Field(default="", description="Fireworks AI API key")
    fireworks_timeout: float = Field(
        default=15.0, ge=1.0, le=120.0, description="Fireworks API request timeout (seconds)"
    )

    # ── Hugging Face Cloud API ────────────────────────────────────────────────
    hf_token: str = Field(default="", description="Hugging Face API token")

    # ── Routing Overrides (from .env) ─────────────────────────────────────────
    math_primary_model: str = Field(default="", description="Math primary model (Hugging Face)")
    math_fallback_model: str = Field(default="", description="Math fallback model (Hugging Face)")
    coding_primary_model: str = Field(default="", description="Coding primary model (Hugging Face)")
    coding_fallback_model: str = Field(
        default="", description="Coding fallback model (Hugging Face)"
    )
    research_primary_model: str = Field(
        default="", description="Research primary model (Hugging Face)"
    )
    research_fallback_model: str = Field(
        default="", description="Research fallback model (Hugging Face)"
    )
    casual_primary_model: str = Field(default="", description="Casual primary model (Hugging Face)")
    casual_fallback_model: str = Field(
        default="", description="Casual fallback model (Hugging Face)"
    )

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite:///./data/metrics.db", description="Database connection URL"
    )
    database_file: str = Field(default="./data/metrics.db", description="SQLite database file path")

    # ── Monitoring ───────────────────────────────────────────────────────────
    prometheus_enabled: bool = Field(
        default=True, description="Expose /metrics endpoint for Prometheus scraping"
    )

    # ── MLflow ───────────────────────────────────────────────────────────────
    mlflow_tracking_uri: str = Field(default="./mlruns", description="MLflow tracking server URI")
    mlflow_experiment_name: str = Field(
        default="router-classifier", description="MLflow experiment name"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Accept comma-separated string or list from environment."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def uppercase_log_level(cls, v: str) -> str:
        return v.upper()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance (singleton). Call this everywhere."""
    return Settings()


# ── Module-level convenience access ─────────────────────────────────────────
# Kept for backwards compatibility with existing imports:
#   from app import config; config.OLLAMA_URL
_s = get_settings()

DEBUG = _s.debug
PORT = _s.port
HOST = _s.host
LOG_LEVEL = _s.log_level
CORS_ORIGINS = _s.cors_origins

OLLAMA_URL = _s.ollama_url
OLLAMA_MODEL = _s.ollama_model
OLLAMA_EMBED_MODEL = _s.ollama_embed_model
OLLAMA_ROUTER_MODEL = _s.ollama_router_model
OLLAMA_TIMEOUT = _s.ollama_timeout

CHROMADB_DIR = _s.chromadb_dir

FIREWORKS_API_KEY = _s.fireworks_api_key
FIREWORKS_TIMEOUT = _s.fireworks_timeout

HF_TOKEN = _s.hf_token

MATH_PRIMARY_MODEL = _s.math_primary_model
MATH_FALLBACK_MODEL = _s.math_fallback_model
CODING_PRIMARY_MODEL = _s.coding_primary_model
CODING_FALLBACK_MODEL = _s.coding_fallback_model
RESEARCH_PRIMARY_MODEL = _s.research_primary_model
RESEARCH_FALLBACK_MODEL = _s.research_fallback_model
CASUAL_PRIMARY_MODEL = _s.casual_primary_model
CASUAL_FALLBACK_MODEL = _s.casual_fallback_model

DATABASE_URL = _s.database_url
DATABASE_FILE = _s.database_file

PROMETHEUS_ENABLED = _s.prometheus_enabled
RATE_LIMIT_ENABLED = _s.rate_limit_enabled
RATE_LIMIT_PER_MINUTE = _s.rate_limit_per_minute
API_KEY_ENABLED = _s.api_key_enabled
API_KEY = _s.api_key

MLFLOW_TRACKING_URI = _s.mlflow_tracking_uri
MLFLOW_EXPERIMENT_NAME = _s.mlflow_experiment_name
