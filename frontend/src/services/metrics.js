import { apiRequest } from './api';

/**
 * Sends a prompt to the router backend for classification and execution.
 * @param {string} prompt 
 * @param {string|null} taskTypeOverride 
 */
export async function processPrompt(prompt, taskTypeOverride = null) {
  return apiRequest('/process', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      task_type: taskTypeOverride,
    }),
  });
}

/**
 * Fetches aggregated performance and cost metrics.
 */
export async function fetchMetrics() {
  return apiRequest('/metrics');
}

/**
 * Fetches backend and model service health.
 */
export async function fetchHealth() {
  return apiRequest('/health');
}
