import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [activity, setActivity] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem('router_activity') || '[]') } catch { return [] }
  })
  const [apiKey, setApiKeyState] = useState(() => sessionStorage.getItem('router_api_key') || '')
  const [compact, setCompact] = useState(() => localStorage.getItem('router_compact') === 'true')
  const [reducedMotion, setReducedMotion] = useState(() => localStorage.getItem('router_motion') === 'reduced')

  useEffect(() => sessionStorage.setItem('router_activity', JSON.stringify(activity.slice(0, 50))), [activity])
  useEffect(() => localStorage.setItem('router_compact', String(compact)), [compact])
  useEffect(() => localStorage.setItem('router_motion', reducedMotion ? 'reduced' : 'full'), [reducedMotion])

  const setApiKey = (value) => {
    setApiKeyState(value)
    if (value) sessionStorage.setItem('router_api_key', value)
    else sessionStorage.removeItem('router_api_key')
  }
  const addActivity = (entry) => setActivity((items) => [{ ...entry, createdAt: new Date().toISOString() }, ...items].slice(0, 50))
  const clearActivity = () => setActivity([])

  const value = useMemo(() => ({ activity, addActivity, clearActivity, apiKey, setApiKey, compact, setCompact, reducedMotion, setReducedMotion }), [activity, apiKey, compact, reducedMotion])
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export const useApp = () => useContext(AppContext)
