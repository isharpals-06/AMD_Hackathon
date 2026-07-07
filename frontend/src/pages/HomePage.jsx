import { useState } from 'react'
import { BrainCircuit, Activity, FlaskConical, BarChart3, ChevronRight, Zap, Shield, Server } from 'lucide-react'

/**
 * HomePage — landing dashboard for the AMD Multi-Model Router.
 * Displays system overview stats and routing category cards.
 */
export default function HomePage({ onNavigate }) {
  const stats = [
    { label: 'Local Tokens Saved', value: '—', icon: Zap, color: 'var(--accent-green)' },
    { label: 'Cloud Fallbacks', value: '—', icon: Shield, color: 'var(--accent-yellow)' },
    { label: 'Avg Latency', value: '— ms', icon: Activity, color: 'var(--accent-blue)' },
    { label: 'Cost Saved (USD)', value: '$—', icon: Server, color: 'var(--accent-purple)' },
  ]

  const routes = [
    { type: 'math', label: 'Math Tasks', model: 'Qwen-72B (Fireworks)', badge: 'Cloud' },
    { type: 'coding', label: 'Coding / Review', model: 'Mixtral 8×7B (Fireworks)', badge: 'Cloud' },
    { type: 'research', label: 'Research (RAG)', model: 'Mixtral 8×7B → Qwen 7B', badge: 'Hybrid' },
    { type: 'casual', label: 'Casual Chat', model: 'Qwen 7B (Ollama — Local)', badge: 'Local' },
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
