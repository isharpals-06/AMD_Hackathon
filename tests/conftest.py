"""
Shared test fixtures for the AMD Multi-Model Router test suite.

Provides:
  - app_client: FastAPI TestClient with mocked Ollama + Fireworks
  - temp_db: Temporary SQLite database
  - mock_ollama_client: Patches OllamaClient methods
  - mock_fireworks_client: Patches FireworksClient methods
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# ── Override database to a temp file before importing the app ─────────────────
@pytest.fixture(scope="session", autouse=True)
def temp_db_env(tmp_path_factory):
    """Point DATABASE_FILE to a temp path and set test-safe defaults."""
    db_dir = tmp_path_factory.mktemp("testdb")
    db_path = str(db_dir / "test_metrics.db")
    os.environ["DATABASE_FILE"] = db_path
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["PROMETHEUS_ENABLED"] = "false"   # no prometheus in tests
    os.environ["RATE_LIMIT_ENABLED"] = "false"   # no rate limiting in tests
    os.environ["API_KEY_ENABLED"] = "false"       # no auth in tests
    os.environ["FIREWORKS_API_KEY"] = "test-key-ci"

    # Clear the lru_cache so the app picks up the new env vars
    try:
        from app.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass

    yield db_path



@pytest.fixture(scope="session")
def app_with_mocks():
    """
    Create the FastAPI app with external services mocked out.

    OllamaClient and FireworksClient are replaced with AsyncMocks
    so tests run without any running services.
    """
    ollama_response = {
        "text": "Mocked Ollama response",
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
    }
    fireworks_response = {
        "text": "Mocked Fireworks response",
        "input_tokens": 15,
        "output_tokens": 25,
        "total_tokens": 40,
    }

    with (
        patch(
            "app.services.ollama_client.OllamaClient.generate",
            new_callable=AsyncMock,
            return_value=ollama_response,
        ),
        patch(
            "app.services.ollama_client.OllamaClient.check_health",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.services.ollama_client.OllamaClient.get_embedding",
            new_callable=AsyncMock,
            return_value=[0.1] * 768,
        ),
        patch(
            "app.services.fireworks_client.FireworksClient.chat_completion",
            new_callable=AsyncMock,
            return_value=fireworks_response,
        ),
        patch(
            "app.services.fireworks_client.FireworksClient.check_health",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        from app.main import app

        yield app


@pytest.fixture(scope="session")
def client(app_with_mocks) -> Generator[TestClient, None, None]:
    """Synchronous TestClient for API endpoint tests."""
    with TestClient(app_with_mocks, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def mock_ollama_generate():
    """Fixture that mocks OllamaClient.generate for a single test."""
    response = {
        "text": "Test response",
        "input_tokens": 5,
        "output_tokens": 10,
        "total_tokens": 15,
    }
    with patch(
        "app.services.ollama_client.OllamaClient.generate",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock:
        yield mock
