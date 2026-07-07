import { useState } from 'react'
import { BrainCircuit, LayoutDashboard, FlaskConical, BarChart3, Activity } from 'lucide-react'
import HomePage from '@/pages/HomePage'
import PlaygroundPage from '@/pages/PlaygroundPage'
import MetricsPage from '@/pages/MetricsPage'
import './App.css'

const NAV_ITEMS = [
  { id: 'home',       label: 'Dashboard',  icon: LayoutDashboard },
  { id: 'playground', label: 'Playground', icon: FlaskConical },
  { id: 'metrics',    label: 'Metrics',    icon: BarChart3 },
]

function App() {
  const [page, setPage] = useState('home')

  const renderPage = () => {
    switch (page) {
      case 'playground': return <PlaygroundPage />
      case 'metrics':    return <MetricsPage />
      default:           return <HomePage onNavigate={setPage} />
    }
  }

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar__brand">
          <BrainCircuit size={24} strokeWidth={1.5} />
          <span>MultiRouter</span>
        </div>

        <nav className="sidebar__nav">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              id={`nav-${id}`}
              className={`nav-item ${page === id ? 'nav-item--active' : ''}`}
              onClick={() => setPage(id)}
            >
              <Icon size={18} strokeWidth={1.5} />
              {label}
            </button>
          ))}
        </nav>

        <div className="sidebar__footer">
          <span className="status-dot status-dot--live" aria-label="System online" />
          <span>AMD ROCm Ready</span>
        </div>
      </aside>

      {/* Main content */}
      <main className="main-content" id="main-content">
        <header className="topbar">
          <div className="topbar__breadcrumb">
            {NAV_ITEMS.find(n => n.id === page)?.label ?? 'Dashboard'}
          </div>
          <div className="topbar__status">
            <Activity size={14} />
            <span>Backend: <strong>/api/health</strong></span>
          </div>
        </header>

        <div className="page-container">
          {renderPage()}
        </div>
      </main>
    </div>
  )
}

export default App
