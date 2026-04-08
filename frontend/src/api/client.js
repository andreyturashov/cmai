const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `Request failed: ${res.status}`);
  }

  return res.json();
}

export const api = {
  getTasks: () => request('/tasks'),
  getTaskById: (id) => request(`/tasks/${id}`),
  createReview: (payload) =>
    request('/reviews', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  evaluate: (payload) =>
    request('/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  aiAnalyze: (payload) =>
    request('/ai-analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
