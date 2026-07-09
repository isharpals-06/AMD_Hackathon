import sqlite3
from unittest.mock import patch

import pytest

from app import database


class ConnectionProxy:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        # Prevent closing during tests
        pass


# Helper to setup in-memory db during test runs
@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes in-memory database and patches the connection function."""
    conn = sqlite3.connect(":memory:")
    # SQLite requires dict row factory to match app.database behavior
    conn.row_factory = sqlite3.Row

    # Initialize tables
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            prompt TEXT,
            task_type TEXT,
            prompt_length INTEGER,
            primary_model TEXT,
            fallback_model_used INTEGER DEFAULT 0,
            final_model_used TEXT,
            status TEXT,
            response TEXT,
            response_length INTEGER,
            tokens_used INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost_usd REAL,
            latency_ms INTEGER,
            error_message TEXT
        )
    """
    )
    conn.commit()

    proxy = ConnectionProxy(conn)

    with patch("app.database.get_db_connection", return_value=proxy):
        yield proxy

    # Clean up the actual connection
    conn.close()


def test_log_request_and_aggregations():
    """Verify log_request writes data and get_aggregate_metrics aggregates values correctly."""
    record = {
        "request_id": "req-1",
        "prompt": "Test query math",
        "task_type": "math",
        "prompt_length": 15,
        "primary_model": "ollama:gemma-4-31b-it",
        "fallback_model_used": 0,
        "final_model_used": "ollama:gemma-4-31b-it",
        "status": "success",
        "response": "Answer is 4",
        "response_length": 11,
        "tokens_used": 20,
        "input_tokens": 12,
        "output_tokens": 8,
        "cost_usd": 0.000024,
        "latency_ms": 1500,
        "error_message": None,
    }

    # Log the request
    database.log_request(record)

    # Fetch metrics
    metrics = database.get_aggregate_metrics()

    assert metrics["total_requests"] == 1
    assert metrics["successful_requests"] == 1
    assert metrics["total_tokens"] == 20
    assert metrics["total_cost"] == 0.000024
    assert metrics["avg_latency_ms"] == 1500.0
    assert metrics["fallback_count"] == 0

    # Verify virtual cost savings calculations are generated
    assert metrics["baseline_cost_usd"] > 0
    assert metrics["cost_saved_usd"] >= 0
