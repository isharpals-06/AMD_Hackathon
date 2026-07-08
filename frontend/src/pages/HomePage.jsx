import { useState, useEffect } from 'react'
import { BrainCircuit, Activity, ChevronRight, Zap, Shield, Server, RefreshCw } from 'lucide-react'

/**
 * HomePage — landing dashboard for the AMD Multi-Model Router.
 * Displays system overview stats and routing category cards.
 */
export default function HomePage({ onNavigate }) {
  const [metrics, setMetrics] = useState(null)
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [metricsRes, configRes] = await Promise.all([
          fetch('/api/metrics'),
          fetch('/api/config')
        ])
        if (metricsRes.ok) {
          const json = await metricsRes.json()
          setMetrics(json.aggregated_metrics)
        }
        if (configRes.ok) {
          const json = await configRes.json()
          setConfig(json.models)
        }
      } catch (err) {
        console.error("Failed to load data on HomePage:", err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const stats = [
    { 
      label: 'Local Tokens Routed', 
      value: metrics ? metrics.local_tokens_used?.toLocaleString() : '—', 
      icon: Zap, 
      color: 'var(--accent-green)' 
    },
    { 
      label: 'Fallback Swaps', 
      value: metrics ? Math.round(metrics.fallback_rate * metrics.total_requests) : '—', 
      icon: Shield, 
      color: 'var(--accent-yellow)' 
    },
    { 
      label: 'Avg Latency', 
      value: metrics ? `${metrics.avg_latency_ms?.toFixed(0)} ms` : '— ms', 
      icon: Activity, 
      color: 'var(--accent-blue)' 
    },
    { 
      label: 'Virtual Cost Saved', 
      value: metrics ? `$${metrics.cost_saved_usd?.toFixed(4)}` : '$—', 
      icon: Server, 
      color: 'var(--accent-purple)' 
    },
  ]

  const getModelLabel = (type) => {
    if (!config || !config[type]) return 'Loading...';
    const primary = config[type].primary || '';
    if (!primary.includes(':')) return primary;
    const [provider, name] = primary.split(':');
    return `${name} (${provider.toUpperCase()})`;
  }

  const getModelBadge = (type) => {
    if (!config || !config[type]) return 'Local';
    const primary = config[type].primary || '';
    if (!primary.includes(':')) return 'Local';
    return primary.startsWith('ollama') ? 'Local' : 'Cloud';
  }

  const routes = [
    { type: 'math', label: 'Math Tasks', model: getModelLabel('math'), badge: getModelBadge('math') },
    { type: 'coding', label: 'Coding / Review', model: getModelLabel('coding'), badge: getModelBadge('coding') },
    { type: 'research', label: 'Research (RAG)', model: getModelLabel('research'), badge: getModelBadge('research') },
    { type: 'casual', label: 'Casual Chat', model: getModelLabel('casual'), badge: getModelBadge('casual') },
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
