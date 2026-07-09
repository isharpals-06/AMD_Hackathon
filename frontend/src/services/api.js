const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Parses validation error arrays or objects into a readable string message.
 */
export function formatErrorDetail(detail) {
  if (!detail) return '';
  if (Array.isArray(detail)) {
    return detail.map(err => {
      // Filter out generic 'body' prefix to make the path prettier (e.g. 'prompt' instead of 'body.prompt')
      const field = err.loc ? err.loc.filter(l => l !== 'body').join('.') : '';
      return `${field ? field + ': ' : ''}${err.msg}`;
    }).join(', ');
  }
  if (typeof detail === 'object') {
    return JSON.stringify(detail);
  }
  return String(detail);
}

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
      errorDetail = formatErrorDetail(errJson.detail) || errJson.error || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return response.json();
}
