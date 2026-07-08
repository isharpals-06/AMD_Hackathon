import os
import sqlite3
from datetime import datetime

DATABASE_FILE = "./data/metrics.db"

def get_db_connection():
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prompt TEXT NOT NULL,
            task_type TEXT,
            prompt_length INTEGER,
            primary_model TEXT,
            fallback_model_used BOOLEAN DEFAULT 0,
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
    """)
    
    # Create indexes for fast querying on the dashboard
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_type ON requests(task_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON requests(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON requests(created_at)")
    
    conn.commit()
    conn.close()

def log_request(request_data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO requests (
            request_id, prompt, task_type, prompt_length, primary_model,
            fallback_model_used, final_model_used, status, response, response_length,
            tokens_used, input_tokens, output_tokens, cost_usd, latency_ms, error_message
        ) VALUES (
            :request_id, :prompt, :task_type, :prompt_length, :primary_model,
            :fallback_model_used, :final_model_used, :status, :response, :response_length,
            :tokens_used, :input_tokens, :output_tokens, :cost_usd, :latency_ms, :error_message
        )
    """, request_data)
    
    conn.commit()
    conn.close()

def get_aggregate_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. General counts and rates
    cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN status LIKE 'success%' THEN 1 ELSE 0 END) as successful_requests,
            SUM(CASE WHEN final_model_used LIKE 'ollama:%' THEN tokens_used ELSE 0 END) as local_tokens,
            SUM(CASE WHEN final_model_used LIKE 'fireworks:%' THEN tokens_used ELSE 0 END) as cloud_tokens,
            SUM(cost_usd) as total_cost,
            AVG(latency_ms) as avg_latency_ms,
            SUM(CASE WHEN fallback_model_used = 1 THEN 1 ELSE 0 END) as fallback_count
        FROM requests
    """)
    row = cursor.fetchone()
    
    total_requests = row["total_requests"] or 0
    successful_requests = row["successful_requests"] or 0
    local_tokens = row["local_tokens"] or 0
    cloud_tokens = row["cloud_tokens"] or 0
    total_cost_usd = row["total_cost"] or 0.0
    avg_latency_ms = row["avg_latency_ms"] or 0.0
    fallback_count = row["fallback_count"] or 0
    
    fallback_rate = fallback_count / total_requests if total_requests > 0 else 0.0
    success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
    
    # 2. Counts by task type
    cursor.execute("SELECT task_type, COUNT(*) as cnt FROM requests GROUP BY task_type")
    task_type_counts = {r["task_type"]: r["cnt"] for r in cursor.fetchall()}
    
    # 3. Avg latency by task type
    cursor.execute("SELECT task_type, AVG(latency_ms) as avg_lat FROM requests GROUP BY task_type")
    avg_latency_by_type = {r["task_type"]: r["avg_lat"] for r in cursor.fetchall()}
    
    metrics = {
        "total_requests": total_requests,
        "total_cost_usd": total_cost_usd,
        "local_tokens_used": local_tokens,
        "cloud_tokens_used": cloud_tokens,
        "fallback_rate": fallback_rate,
        "success_rate": success_rate,
        "avg_latency_ms": avg_latency_ms,
        "task_type_counts": task_type_counts,
        "avg_latency_by_type": avg_latency_by_type
    }
    
    # Calculate savings vs baseline
    cursor.execute("""
        SELECT 
            SUM(input_tokens) as total_input,
            SUM(output_tokens) as total_output
        FROM requests
        WHERE status LIKE 'success%'
    """)
    totals = cursor.fetchone()
    if totals and totals["total_input"] is not None:
        # Baseline cost calculation: assuming gemma-4-31b-it rates for all as baseline ($1.20 per 1M tokens)
        baseline_rate = 1.20 / 1000000.0
        total_tokens = totals["total_input"] + totals["total_output"]
        baseline_cost = total_tokens * baseline_rate
        metrics["baseline_cost_usd"] = baseline_cost
        metrics["cost_saved_usd"] = max(0.0, baseline_cost - total_cost_usd)
        metrics["savings_pct"] = (metrics["cost_saved_usd"] / baseline_cost * 100) if baseline_cost > 0 else 0.0
    else:
        metrics["baseline_cost_usd"] = 0.0
        metrics["cost_saved_usd"] = 0.0
        metrics["savings_pct"] = 0.0
        
    conn.close()
    return metrics
