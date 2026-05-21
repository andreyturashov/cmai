const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include',
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
  getAuthSession: () => request('/auth/session'),
  loginWithGoogle: (payload) =>
    request('/auth/google', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  logout: () =>
    request('/auth/logout', {
      method: 'POST',
    }),
  getUserInterests: () => request('/me/interests'),
  updateUserInterests: (payload) =>
    request('/me/interests', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  getTaskSchedule: () => request('/me/task-schedule'),
  regenerateTaskSchedule: () =>
    request('/me/task-schedule/regenerate', {
      method: 'POST',
    }),
  getTasks: (language) => {
    const params = language ? `?language=${encodeURIComponent(language)}` : '';
    return request(`/tasks${params}`);
  },
  getTaskById: (id) => request(`/tasks/${id}`),
  getUserProgress: () => request('/me/progress'),
  getUserProgressDaily: () => request('/me/progress/daily'),
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
