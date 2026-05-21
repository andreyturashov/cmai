import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from './client';

const BASE_URL = 'http://localhost:8000';

describe('api client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('getTasks fetches tasks without language filter', async () => {
    const mockTasks = [{ id: 'task-1', title: 'Task 1' }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockTasks),
    });

    const result = await api.getTasks();
    expect(fetch).toHaveBeenCalledWith(
      `${BASE_URL}/tasks`,
      expect.objectContaining({
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      }),
    );
    expect(result).toEqual(mockTasks);
  });

  it('getTasks passes language query param', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    await api.getTasks('javascript');
    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/tasks?language=javascript`, expect.anything());
  });

  it('getTaskById fetches a single task', async () => {
    const task = { id: 'task-1', title: 'Task 1', code: 'print()' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(task),
    });

    const result = await api.getTaskById('task-1');
    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/tasks/task-1`, expect.anything());
    expect(result).toEqual(task);
  });

  it('createReview sends POST with payload', async () => {
    const payload = { task_id: 't1', comments: [] };
    const review = { id: 'r1', ...payload };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(review),
    });

    const result = await api.createReview(payload);
    expect(fetch).toHaveBeenCalledWith(
      `${BASE_URL}/reviews`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    );
    expect(result).toEqual(review);
  });

  it('evaluate sends POST', async () => {
    const payload = { review_id: 'r1', task_id: 't1' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ score: 8 }),
    });

    const result = await api.evaluate(payload);
    expect(fetch).toHaveBeenCalledWith(
      `${BASE_URL}/evaluate`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    );
    expect(result).toEqual({ score: 8 });
  });

  it('aiAnalyze sends POST', async () => {
    const payload = { review_id: 'r1' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ analysis: {} }),
    });

    const result = await api.aiAnalyze(payload);
    expect(fetch).toHaveBeenCalledWith(
      `${BASE_URL}/ai-analyze`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    );
    expect(result).toEqual({ analysis: {} });
  });

  it('getUserProgress fetches the authenticated user progress list', async () => {
    const progress = [{ id: 1, task_id: 'task-1' }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(progress),
    });

    const result = await api.getUserProgress();
    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/me/progress`, expect.anything());
    expect(result).toEqual(progress);
  });

  it('getUserProgressDaily fetches the authenticated user progress summary by day', async () => {
    const progress = [{ day: '2026-05-20', completed_tasks: 2 }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(progress),
    });

    const result = await api.getUserProgressDaily();
    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/me/progress/daily`, expect.anything());
    expect(result).toEqual(progress);
  });

  it('getUserInterests fetches the authenticated user interests', async () => {
    const interests = { interests: ['python_theory', 'javascript'] };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(interests),
    });

    const result = await api.getUserInterests();
    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/me/interests`, expect.anything());
    expect(result).toEqual(interests);
  });

  it('updateUserInterests sends PUT with payload', async () => {
    const payload = { interests: ['python_theory', 'react'] };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(payload),
    });

    const result = await api.updateUserInterests(payload);
    expect(fetch).toHaveBeenCalledWith(
      `${BASE_URL}/me/interests`,
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
    );
    expect(result).toEqual(payload);
  });

  it('getTaskSchedule fetches the authenticated task schedule', async () => {
    const schedule = { tasks: [{ id: 'task-1', title: 'Task 1' }] };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(schedule),
    });

    const result = await api.getTaskSchedule();
    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/me/task-schedule`, expect.anything());
    expect(result).toEqual(schedule);
  });

  it('regenerateTaskSchedule sends POST', async () => {
    const schedule = { tasks: [{ id: 'task-2', title: 'Task 2' }] };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(schedule),
    });

    const result = await api.regenerateTaskSchedule();
    expect(fetch).toHaveBeenCalledWith(
      `${BASE_URL}/me/task-schedule/regenerate`,
      expect.objectContaining({ method: 'POST' }),
    );
    expect(result).toEqual(schedule);
  });

  it('throws on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      text: () => Promise.resolve('Not Found'),
    });

    await expect(api.getTaskById('bad')).rejects.toThrow('Not Found');
  });

  it('throws with status code when body is empty', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve(''),
    });

    await expect(api.getTasks()).rejects.toThrow('Request failed: 500');
  });

  it('getTasks encodes special characters in language', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    await api.getTasks('c++');
    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/tasks?language=c%2B%2B`, expect.anything());
  });
});
