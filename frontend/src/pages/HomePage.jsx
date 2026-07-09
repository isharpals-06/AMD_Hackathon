import { useState, useEffect } from 'react'
import { BrainCircuit, Activity, ChevronRight, Zap, Shield, Server, RefreshCw } from 'lucide-react'

/**
 * HomePage — landing dashboard for the AMD Multi-Model Router.
 * Displays system overview stats and routing category cards.
 */
export default function HomePage({ onNavigate }) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadStats() {
      try {
        const res = await fetch('/api/metrics/summary')
        if (res.ok) {
          const json = await res.json()
          setMetrics(json.aggregated_metrics)
        }
      } catch (err) {
        console.error("Failed to load metrics on HomePage:", err)
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [])

  const stats = [
    { 
      label: 'Total Requests', 
      value: metrics ? (metrics.total_requests ?? 0).toLocaleString() : '—', 
      icon: Zap, 
      color: 'var(--accent-green)' 
    },
    { 
      label: 'Fallback Count', 
      value: metrics ? (metrics.fallback_count ?? 0).toLocaleString() : '—', 
      icon: Shield, 
      color: 'var(--accent-yellow)' 
    },
    { 
      label: 'Avg Latency', 
      value: metrics ? `${(metrics.avg_latency_ms ?? 0).toFixed(0)} ms` : '— ms', 
      icon: Activity, 
      color: 'var(--accent-blue)' 
    },
    { 
      label: 'Cost Saved', 
      value: metrics ? `$${(metrics.cost_saved_usd ?? 0).toFixed(4)}` : '$—', 
      icon: Server, 
      color: 'var(--accent-purple)' 
    },
  ]

  const routes = [
    { type: 'math', label: 'Math Tasks', model: 'Gemma-4-31B-it (Ollama)', badge: 'Local' },
    { type: 'coding', label: 'Coding / Review', model: 'Kimi-K2P7-Code (Ollama)', badge: 'Local' },
    { type: 'research', label: 'Research (RAG)', model: 'Gemma-4-26B-a4b-it (Ollama)', badge: 'Local' },
    { type: 'casual', label: 'Casual Chat', model: 'Minimax-M3 (Ollama)', badge: 'Local' },
  ]

  return (
    <div className="page home-page">
      <div className="page-hero">
        <div className="page-hero__badge">AMD ROCm · Hackathon Track 1</div>
        <h1 className="page-hero__title">
          <BrainCircuit size={32} strokeWidth={1.5} />
          Multi-Model Router
        </h1>
        <p className="page-hero__subtitle">
          Intelligently routes prompts between local SLMs and cloud APIs to maximise performance and minimise cost.
        </p>
        <div className="page-hero__actions">
          <button className="btn btn--primary" onClick={() => onNavigate('playground')}>
            Open Playground <ChevronRight size={16} />
          </button>
          <button className="btn btn--ghost" onClick={() => onNavigate('metrics')}>
            View Metrics
          </button>
        </div>
      </div>

      <div className="stats-grid">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div className="stat-card" key={label}>
            <div className="stat-card__icon" style={{ color }}>
              <Icon size={22} strokeWidth={1.5} />
            </div>
            <div className="stat-card__value">{value}</div>
            <div className="stat-card__label">{label}</div>
          </div>
        ))}
      </div>

      <section className="routes-section">
        <h2 className="section-title">Routing Table</h2>
        <div className="routes-grid">
          {routes.map(({ type, label, model, badge }) => (
            <div className="route-card" key={type} data-type={type}>
              <div className="route-card__header">
                <span className="route-card__label">{label}</span>
                <span className={`route-badge route-badge--${badge.toLowerCase()}`}>{badge}</span>
              </div>
              <div className="route-card__model">{model}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
