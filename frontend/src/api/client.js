import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const key = sessionStorage.getItem('router_api_key')
  if (key) config.headers['X-API-Key'] = key
  return config
})

export const endpoints = {
  health: () => api.get('/health'),
  version: () => api.get('/version'),
  metrics: () => api.get('/metrics/summary'),
  models: () => api.get('/metrics/models'),
  process: (payload, signal) => api.post('/process', payload, { signal }),
}

export function normalizeError(error) {
  if (error.code === 'ERR_CANCELED') return { title: 'Request cancelled', detail: 'The request was cancelled.' }
  if (!error.response) return { title: 'Backend unavailable', detail: 'Start the FastAPI server on port 8000 and try again.' }
  const data = error.response.data || {}
  return {
    title: data.error || data.detail || `Request failed (${error.response.status})`,
    detail: typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || data),
    attempts: data.attempts || [],
    status: error.response.status,
  }
}
