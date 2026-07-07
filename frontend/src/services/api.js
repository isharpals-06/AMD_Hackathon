const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Standard fetch wrapper for backend API calls.
 */
export async function apiRequest(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API Request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.error || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}
