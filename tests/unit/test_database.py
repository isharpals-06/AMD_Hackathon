"""
Unit tests for app.database — SQLite database layer.
"""

from __future__ import annotations

import sqlite3

import pytest

import app.database as db_module


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    """Redirect all DB operations to a fresh temp database per test."""
    db_path = str(tmp_path / "test_metrics.db")
    monkeypatch.setattr(db_module, "DATABASE_FILE", db_path)
    yield db_path


@pytest.mark.unit
class TestInitDb:
    """Tests for database initialisation."""

    def test_creates_requests_table(self, temp_database):
        db_module.init_db()
        conn = sqlite3.connect(temp_database)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='requests'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_creates_indexes(self, temp_database):
        db_module.init_db()
        conn = sqlite3.connect(temp_database)
        indexes = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
        index_names = {row[0] for row in indexes}
        assert "idx_task_type" in index_names
        assert "idx_status" in index_names
        assert "idx_created_at" in index_names
        conn.close()

    def test_idempotent(self, temp_database):
        """Calling init_db() twice should not raise."""
        db_module.init_db()
        db_module.init_db()


@pytest.mark.unit
class TestLogRequest:
    """Tests for log_request()."""

    SAMPLE_RECORD = {
        "request_id": "test-uuid-1234",
        "prompt": "Test prompt for routing",
        "task_type": "coding",
        "prompt_length": 25,
        "primary_model": "ollama:kimi-k2p7-code",
        "fallback_model_used": 0,
        "final_model_used": "ollama:kimi-k2p7-code",
        "status": "success",
        "response": "Here is the code...",
        "response_length": 18,
        "tokens_used": 30,
        "input_tokens": 10,
        "output_tokens": 20,
        "cost_usd": 0.0000105,
        "latency_ms": 1234,
        "error_message": None,
    }

    def test_log_request_inserts_row(self, temp_database):
        db_module.init_db()
        db_module.log_request(self.SAMPLE_RECORD)

        conn = sqlite3.connect(temp_database)
        row = conn.execute(
            "SELECT * FROM requests WHERE request_id = ?", ("test-uuid-1234",)
        ).fetchone()
        assert row is not None
        conn.close()

    def test_logged_values_are_correct(self, temp_database):
        db_module.init_db()
        db_module.log_request(self.SAMPLE_RECORD)

        conn = sqlite3.connect(temp_database)
        conn.row_factory = sqlite3.Row
        row = dict(
            conn.execute(
                "SELECT * FROM requests WHERE request_id = ?", ("test-uuid-1234",)
            ).fetchone()
        )
        assert row["task_type"] == "coding"
        assert row["tokens_used"] == 30
        assert row["status"] == "success"
        conn.close()


@pytest.mark.unit
class TestGetAggregateMetrics:
    """Tests for get_aggregate_metrics()."""

    def test_empty_db_returns_zero_metrics(self, temp_database):
        db_module.init_db()
        metrics = db_module.get_aggregate_metrics()
        # Keys should exist
        assert "total_requests" in metrics
        assert "cost_saved_usd" in metrics
        assert "savings_pct" in metrics

    def test_metrics_reflect_logged_requests(self, temp_database):
        db_module.init_db()
        record = {
            "request_id": "uuid-metrics-test",
            "prompt": "Hello test",
            "task_type": "casual_chat",
            "prompt_length": 10,
            "primary_model": "ollama:minimax-m3",
            "fallback_model_used": 0,
            "final_model_used": "ollama:minimax-m3",
            "status": "success",
            "response": "Hi!",
            "response_length": 3,
            "tokens_used": 50,
            "input_tokens": 20,
            "output_tokens": 30,
            "cost_usd": 0.000002,
            "latency_ms": 500,
            "error_message": None,
        }
        db_module.log_request(record)
        metrics = db_module.get_aggregate_metrics()

        assert metrics["total_requests"] == 1
        assert metrics["successful_requests"] == 1
        assert metrics["total_tokens"] == 50
