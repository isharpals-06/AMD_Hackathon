import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { RefreshCw, Loader2 } from 'lucide-react'

const ROUTE_COLORS = {
  math: '#818cf8',
  coding: '#34d399',
  research: '#f59e0b',
  casual_chat: '#60a5fa',
}

/**
 * MetricsPage — displays aggregated performance and cost analytics
 * fetched from the backend /metrics endpoint.
 */
export default function MetricsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchMetrics = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/metrics/summary')
      if (!res.ok) throw new Error('Failed to fetch metrics')
      const json = await res.json()
      setData(json.aggregated_metrics)
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchMetrics() }, [])

  return (
    <div className="page metrics-page">
      <div className="page-header">
        <div>
          <h1>Metrics</h1>
          <p>Real-time performance and cost analytics across all routing decisions.</p>
        </div>
        <button className="btn btn--ghost" onClick={fetchMetrics} disabled={loading}>
          {loading ? <Loader2 size={14} className="spin" /> : <RefreshCw size={14} />}
          Refresh
        </button>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      {lastUpdated && (
        <p className="metrics-timestamp">Last updated: {lastUpdated}</p>
      )}

      {loading && !data && (
        <div className="metrics-loading">
          <Loader2 size={32} className="spin" />
          <span>Loading metrics…</span>
        </div>
      )}

      {data && (
        <div className="metrics-grid">
          {/* Task Type Distribution Chart */}
          <div className="chart-card">
            <h2>Requests by Task Type</h2>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={Object.entries(data.task_type_counts || {}).map(([name, value]) => ({ name, value }))}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {Object.keys(data.task_type_counts || {}).map((key) => (
                    <Cell key={key} fill={ROUTE_COLORS[key] || '#94a3b8'} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Avg Latency by Task Type */}
          <div className="chart-card">
            <h2>Avg Latency by Task Type (ms)</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={Object.entries(data.avg_latency_by_type || {}).map(([name, value]) => ({ name, value: Math.round(value) }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                <Bar dataKey="value" fill="#818cf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Summary Stats */}
          <div className="chart-card summary-card">
            <h2>Summary</h2>
            <div className="summary-stats">
              <div className="summary-stat">
                <span className="summary-stat__label">Total Requests</span>
                <span className="summary-stat__value">{data.total_requests ?? '—'}</span>
              </div>
              <div className="summary-stat">
                <span className="summary-stat__label">Total Cost (USD)</span>
                <span className="summary-stat__value">${data.total_cost_usd?.toFixed(4) ?? '—'}</span>
              </div>
              <div className="summary-stat">
                <span className="summary-stat__label">Local Tokens</span>
                <span className="summary-stat__value">{data.local_tokens_used ?? '—'}</span>
              </div>
              <div className="summary-stat">
                <span className="summary-stat__label">Cloud Tokens</span>
                <span className="summary-stat__value">{data.cloud_tokens_used ?? '—'}</span>
              </div>
              <div className="summary-stat">
                <span className="summary-stat__label">Fallback Rate</span>
                <span className="summary-stat__value">{data.fallback_rate != null ? `${(data.fallback_rate * 100).toFixed(1)}%` : '—'}</span>
              </div>
              <div className="summary-stat">
                <span className="summary-stat__label">Success Rate</span>
                <span className="summary-stat__value">{data.success_rate != null ? `${(data.success_rate * 100).toFixed(1)}%` : '—'}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
