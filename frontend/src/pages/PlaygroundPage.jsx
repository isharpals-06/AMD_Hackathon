import { useState, useRef } from 'react'
import { Send, Loader2, RotateCcw } from 'lucide-react'

const TASK_TYPES = [
  { value: '', label: 'Auto-detect' },
  { value: 'math', label: 'Math' },
  { value: 'coding', label: 'Coding' },
  { value: 'research', label: 'Research (RAG)' },
  { value: 'casual_chat', label: 'Casual Chat' },
]

/**
 * PlaygroundPage — interactive prompt-testing interface.
 * Sends prompts to /process and displays the routing decision + response.
 */
export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState('')
  const [taskType, setTaskType] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const textareaRef = useRef(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!prompt.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, task_type: taskType || undefined }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Request failed')
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setPrompt('')
    setTaskType('')
    setResult(null)
    setError(null)
    textareaRef.current?.focus()
  }

  return (
    <div className="page playground-page">
      <div className="page-header">
        <h1>Playground</h1>
        <p>Test prompts against the router and see live routing decisions.</p>
      </div>

      <div className="playground-layout">
        {/* Input Panel */}
        <form className="panel input-panel" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="task-type-select">Task Type</label>
            <select
              id="task-type-select"
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="select"
            >
              {TASK_TYPES.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          <div className="form-group form-group--grow">
            <label htmlFor="prompt-textarea">Prompt</label>
            <textarea
              id="prompt-textarea"
              ref={textareaRef}
              className="textarea"
              placeholder="Enter your prompt here..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={10}
              required
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn--ghost" onClick={handleReset}>
              <RotateCcw size={14} /> Reset
            </button>
            <button type="submit" className="btn btn--primary" disabled={loading || !prompt.trim()}>
              {loading ? <Loader2 size={14} className="spin" /> : <Send size={14} />}
              {loading ? 'Routing…' : 'Send'}
            </button>
          </div>
        </form>

        {/* Output Panel */}
        <div className="panel output-panel">
          {!result && !error && !loading && (
            <div className="output-panel__empty">
              <p>Response will appear here after you submit a prompt.</p>
            </div>
          )}

          {loading && (
            <div className="output-panel__loading">
              <Loader2 size={28} className="spin" />
              <span>Processing…</span>
            </div>
          )}

          {error && (
            <div className="output-panel__error">
              <strong>Error:</strong> {error}
            </div>
          )}

          {result && (
            <>
              <div className="result-meta">
                <div className="meta-chip">Task: <strong>{result.metadata?.task_type}</strong></div>
                <div className="meta-chip">Model: <strong>{result.metadata?.final_model_used}</strong></div>
                <div className="meta-chip">Latency: <strong>{result.metadata?.latency_ms} ms</strong></div>
                <div className="meta-chip">Tokens: <strong>{result.tokens?.total}</strong></div>
                <div className="meta-chip">Cost: <strong>${result.cost?.usd?.toFixed(6)}</strong></div>
                {result.metadata?.fallback_model_used && (
                  <div className="meta-chip meta-chip--warn">Fallback Used</div>
                )}
              </div>
              <div className="result-response">
                <pre>{result.result}</pre>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
