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
    
    # Get general counts
    cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN status LIKE 'success%' THEN 1 ELSE 0 END) as successful_requests,
            SUM(tokens_used) as total_tokens,
            SUM(cost_usd) as total_cost,
            AVG(latency_ms) as avg_latency_ms,
            SUM(CASE WHEN fallback_model_used = 1 THEN 1 ELSE 0 END) as fallback_count
        FROM requests
    """)
    row = cursor.fetchone()
    metrics = dict(row) if row else {}
    
    # Calculate savings vs baseline (assuming Fireworks Mixtral for all as baseline)
    # Baseline cost: $0.0005 per 1k input tokens, $0.0015 per 1k output tokens
    cursor.execute("""
        SELECT 
            SUM(input_tokens) as total_input,
            SUM(output_tokens) as total_output
        FROM requests
        WHERE status LIKE 'success%'
    """)
    totals = cursor.fetchone()
    if totals and totals["total_input"] is not None:
        baseline_cost = (totals["total_input"] * 0.0005 / 1000) + (totals["total_output"] * 0.0015 / 1000)
        actual_cost = metrics.get("total_cost", 0) or 0
        metrics["baseline_cost_usd"] = baseline_cost
        metrics["cost_saved_usd"] = max(0.0, baseline_cost - actual_cost)
        metrics["savings_pct"] = (metrics["cost_saved_usd"] / baseline_cost * 100) if baseline_cost > 0 else 0
    else:
        metrics["baseline_cost_usd"] = 0
        metrics["cost_saved_usd"] = 0
        metrics["savings_pct"] = 0
        
    conn.close()
    return metrics
