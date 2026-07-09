"""
SQLite database layer for request logging and metrics aggregation.

Improvements over v1:
  - Reads database path from config (no more hardcoded strings)
  - Uses context manager for safer connection handling
  - Added get_per_model_metrics() for Grafana dashboards
  - Added type annotations
"""
from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Generator

from app import config

logger = logging.getLogger(__name__)

# ── Database path from config (no more hardcoded paths) ──────────────────────
DATABASE_FILE: str = config.DATABASE_FILE


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager that yields an open SQLite connection and closes it on exit."""
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE_FILE)), exist_ok=True)
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Create the requests table and indexes if they do not already exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                request_id      TEXT PRIMARY KEY,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                prompt          TEXT NOT NULL,
                task_type       TEXT,
                prompt_length   INTEGER,
                primary_model   TEXT,
                fallback_model_used  BOOLEAN DEFAULT 0,
                final_model_used     TEXT,
                status          TEXT,
                response        TEXT,
                response_length INTEGER,
                tokens_used     INTEGER,
                input_tokens    INTEGER,
                output_tokens   INTEGER,
                cost_usd        REAL,
                latency_ms      INTEGER,
                error_message   TEXT
            )
        """)

        # Indexes for fast querying on the dashboard
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_type ON requests(task_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status   ON requests(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON requests(created_at)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_final_model ON requests(final_model_used)"
        )

        conn.commit()
    logger.info("Database initialised at %s", DATABASE_FILE)


def log_request(request_data: dict[str, Any]) -> None:
    """Insert a completed request record into the requests table."""
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO requests (
                request_id, prompt, task_type, prompt_length, primary_model,
                fallback_model_used, final_model_used, status, response,
                response_length, tokens_used, input_tokens, output_tokens,
                cost_usd, latency_ms, error_message
            ) VALUES (
                :request_id, :prompt, :task_type, :prompt_length, :primary_model,
                :fallback_model_used, :final_model_used, :status, :response,
                :response_length, :tokens_used, :input_tokens, :output_tokens,
                :cost_usd, :latency_ms, :error_message
            )
            """,
            request_data,
        )
        conn.commit()


def get_aggregate_metrics() -> dict[str, Any]:
    """Return aggregated performance and cost-savings metrics.

    Includes per-task-type breakdowns that the frontend dashboard expects.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*)                                                        AS total_requests,
                SUM(CASE WHEN status LIKE 'success%' THEN 1 ELSE 0 END)        AS successful_requests,
                SUM(tokens_used)                                                AS total_tokens,
                SUM(cost_usd)                                                   AS total_cost,
                AVG(latency_ms)                                                 AS avg_latency_ms,
                SUM(CASE WHEN fallback_model_used = 1 THEN 1 ELSE 0 END)       AS fallback_count
            FROM requests
        """)
        row = cursor.fetchone()
        metrics: dict[str, Any] = dict(row) if row else {}

        total = metrics.get("total_requests") or 0
        success = metrics.get("successful_requests") or 0
        fallback = metrics.get("fallback_count") or 0

        # ── Derived rates ────────────────────────────────────────────────
        metrics["success_rate"] = round(success / total, 4) if total > 0 else 0.0
        metrics["fallback_rate"] = round(fallback / total, 4) if total > 0 else 0.0
        metrics["total_cost_usd"] = metrics.get("total_cost") or 0.0

        # ── Per-task-type counts ─────────────────────────────────────────
        cursor.execute("""
            SELECT task_type, COUNT(*) AS cnt
            FROM requests
            WHERE task_type IS NOT NULL
            GROUP BY task_type
        """)
        metrics["task_type_counts"] = {r["task_type"]: r["cnt"] for r in cursor.fetchall()}

        # ── Avg latency by task type ─────────────────────────────────────
        cursor.execute("""
            SELECT task_type, AVG(latency_ms) AS avg_lat
            FROM requests
            WHERE task_type IS NOT NULL
            GROUP BY task_type
        """)
        metrics["avg_latency_by_type"] = {
            r["task_type"]: round(r["avg_lat"], 1) for r in cursor.fetchall()
        }

        # ── Token breakdown: local (ollama) vs cloud (huggingface/fireworks) ─
        cursor.execute("""
            SELECT
                SUM(CASE WHEN final_model_used LIKE 'ollama:%' THEN tokens_used ELSE 0 END)       AS local_tokens,
                SUM(CASE WHEN final_model_used NOT LIKE 'ollama:%' THEN tokens_used ELSE 0 END)   AS cloud_tokens
            FROM requests
            WHERE status LIKE 'success%'
        """)
        token_row = cursor.fetchone()
        metrics["local_tokens_used"] = (token_row["local_tokens"] or 0) if token_row else 0
        metrics["cloud_tokens_used"] = (token_row["cloud_tokens"] or 0) if token_row else 0

        # ── Cost-savings vs. always-Fireworks baseline ───────────────────
        cursor.execute("""
            SELECT SUM(input_tokens) AS total_input, SUM(output_tokens) AS total_output
            FROM requests
            WHERE status LIKE 'success%'
        """)
        totals = cursor.fetchone()
        if totals and totals["total_input"] is not None:
            baseline_cost = (totals["total_input"] * 0.0005 / 1000) + (
                totals["total_output"] * 0.0015 / 1000
            )
            actual_cost = metrics.get("total_cost") or 0.0
            metrics["baseline_cost_usd"] = round(baseline_cost, 6)
            metrics["cost_saved_usd"] = round(max(0.0, baseline_cost - actual_cost), 6)
            metrics["savings_pct"] = (
                round(metrics["cost_saved_usd"] / baseline_cost * 100, 2) if baseline_cost > 0 else 0.0
            )
        else:
            metrics["baseline_cost_usd"] = 0.0
            metrics["cost_saved_usd"] = 0.0
            metrics["savings_pct"] = 0.0

        return metrics


def get_per_model_metrics() -> list[dict[str, Any]]:
    """Return per-model breakdown: request count, avg latency, total cost."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                final_model_used                AS model,
                COUNT(*)                        AS request_count,
                AVG(latency_ms)                 AS avg_latency_ms,
                SUM(cost_usd)                   AS total_cost_usd,
                SUM(tokens_used)                AS total_tokens
            FROM requests
            WHERE final_model_used IS NOT NULL
            GROUP BY final_model_used
            ORDER BY request_count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
