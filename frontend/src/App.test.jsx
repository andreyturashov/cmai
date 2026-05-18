import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the api module
vi.mock('./api/client', () => ({
  api: {
    getTasks: vi.fn(),
    getTaskById: vi.fn(),
    createReview: vi.fn(),
    aiAnalyze: vi.fn(),
  },
}));

import App from './App';
import { api } from './api/client';

const taskSummary = { id: 'task-1', title: 'Validate Input', language: 'python' };
const fullTask = {
  id: 'task-1',
  title: 'Validate Input',
  description: 'Check user registration fields',
  language: 'python',
  code: 'def register(name):\n    pass',
  requirements: ['Validate name'],
  reference_issues: [],
};

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getTasks.mockResolvedValue([taskSummary]);
    api.getTaskById.mockResolvedValue(fullTask);
  });

  it('renders the header', async () => {
    render(<App />);
    expect(screen.getByText('Code Mentor')).toBeInTheDocument();
    await waitFor(() => expect(api.getTasks).toHaveBeenCalled());
  });

  it('loads tasks on mount for default language', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python'));
    await waitFor(() => expect(api.getTaskById).toHaveBeenCalledWith('task-1'));
  });

  it('renders language toggle buttons', async () => {
    render(<App />);
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('Python (questions)')).toBeInTheDocument();
    expect(screen.getByText('Python (theory)')).toBeInTheDocument();
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
    await waitFor(() => expect(api.getTasks).toHaveBeenCalled());
  });

  it('switches to Python questions language', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python'));

    api.getTasks.mockResolvedValue([
      { id: 'py-q-1', title: 'Simple Python Question', language: 'python_questions' },
    ]);
    api.getTaskById.mockResolvedValue({
      ...fullTask,
      id: 'py-q-1',
      title: 'Simple Python Question',
      language: 'python_questions',
    });

    await userEvent.click(screen.getByText('Python (questions)'));
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python_questions'));
  });

  it('switches to Python theory language', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python'));

    api.getTasks.mockResolvedValue([
      { id: 'theory-1', title: 'List vs tuple', language: 'python_theory' },
    ]);
    api.getTaskById.mockResolvedValue({
      ...fullTask,
      id: 'theory-1',
      title: 'List vs tuple',
      language: 'python_theory',
      submission_mode: 'answer',
      code: '# Python theory question',
    });

    await userEvent.click(screen.getByText('Python (theory)'));
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python_theory'));
  });

  it('submits a theory answer for analysis', async () => {
    api.getTasks.mockResolvedValue([
      { id: 'theory-1', title: 'List vs tuple', language: 'python_theory' },
    ]);
    api.getTaskById.mockResolvedValue({
      ...fullTask,
      id: 'theory-1',
      title: 'List vs tuple',
      language: 'python_theory',
      submission_mode: 'answer',
      instructions: ['Answer the question'],
      code: '# Python theory question',
    });
    api.createReview.mockResolvedValue({ id: 'r1' });
    api.aiAnalyze.mockResolvedValue({
      analysis: {
        all_fixed: true,
        score: 9,
        detected_critical: 0,
        total_critical: 0,
        detected_medium: 1,
        total_medium: 1,
        detected_low: 0,
        total_low: 0,
        missed_issues: [],
        feedback: ['Good answer'],
        summary: 'Clear answer.',
        issues: [],
      },
    });

    render(<App />);
    await userEvent.click(screen.getByText('Python (theory)'));
    await waitFor(() => expect(screen.getByText('Your Answer')).toBeInTheDocument());

    await userEvent.type(
      screen.getByPlaceholderText('Write your answer here'),
      'Lists are mutable.',
    );
    await userEvent.click(screen.getByText('Submit Review'));

    await waitFor(() =>
      expect(api.createReview).toHaveBeenCalledWith(
        expect.objectContaining({ answer: 'Lists are mutable.' }),
      ),
    );
  });

  it('switches language when button clicked', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python'));

    api.getTasks.mockResolvedValue([{ id: 'js-1', title: 'JS Task', language: 'javascript' }]);
    api.getTaskById.mockResolvedValue({ ...fullTask, id: 'js-1', language: 'javascript' });

    await userEvent.click(screen.getByText('JavaScript'));
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('javascript'));
  });

  it('shows task content once loaded', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Validate Input')).toBeInTheDocument();
    });
  });

  it('renders Next Task button', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalled());
    expect(screen.getByText('Next Task')).toBeInTheDocument();
  });

  it('shows error banner on API failure', async () => {
    api.getTasks.mockRejectedValue(new Error('Network error'));
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('handles Next Task click', async () => {
    const tasks = [
      { id: 'task-1', title: 'T1', language: 'python' },
      { id: 'task-2', title: 'T2', language: 'python' },
    ];
    // Shuffle is random, mock to return as-is by mocking Math.random
    vi.spyOn(Math, 'random').mockReturnValue(0.99);
    api.getTasks.mockResolvedValue(tasks);
    api.getTaskById
      .mockResolvedValueOnce({ ...fullTask, id: 'task-1', title: 'T1' })
      .mockResolvedValueOnce({ ...fullTask, id: 'task-2', title: 'T2' });

    render(<App />);
    await waitFor(() => expect(screen.getByText('T1')).toBeInTheDocument());

    await userEvent.click(screen.getByText('Next Task'));
    await waitFor(() => expect(screen.getByText('T2')).toBeInTheDocument());

    Math.random.mockRestore();
  });

  it('submits review and shows AI analysis', async () => {
    api.createReview.mockResolvedValue({ id: 'r1' });
    api.aiAnalyze.mockResolvedValue({
      analysis: {
        all_fixed: true,
        score: 9,
        detected_critical: 1,
        total_critical: 1,
        detected_medium: 0,
        total_medium: 0,
        detected_low: 0,
        total_low: 0,
        missed_issues: [],
        feedback: ['Great job!'],
        summary: 'Well done.',
        issues: [],
      },
    });

    render(<App />);
    await waitFor(() => expect(screen.getByText('Validate Input')).toBeInTheDocument());

    await userEvent.click(screen.getByText('Submit Review'));
    await waitFor(() => {
      expect(screen.getByText('✓ All issues addressed')).toBeInTheDocument();
    });
  });

  it('shows error state when AI analysis fails', async () => {
    api.createReview.mockRejectedValue(new Error('AI unavailable'));

    render(<App />);
    await waitFor(() => expect(screen.getByText('Validate Input')).toBeInTheDocument());

    await userEvent.click(screen.getByText('Submit Review'));
    await waitFor(() => {
      expect(screen.getByText('AI analysis unavailable')).toBeInTheDocument();
    });
  });

  it('wraps around to first task on Next after last', async () => {
    const tasks = [{ id: 'task-1', title: 'Only Task', language: 'python' }];
    vi.spyOn(Math, 'random').mockReturnValue(0.99);
    api.getTasks.mockResolvedValue(tasks);
    api.getTaskById.mockResolvedValue(fullTask);

    render(<App />);
    await waitFor(() => expect(screen.getByText('Validate Input')).toBeInTheDocument());

    await userEvent.click(screen.getByText('Next Task'));
    // Should wrap to index 0 — same task
    await waitFor(() => expect(api.getTaskById).toHaveBeenCalledWith('task-1'));

    Math.random.mockRestore();
  });

  it('shows error when getTaskById fails', async () => {
    api.getTaskById.mockRejectedValue(new Error('Task not found'));
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Task not found')).toBeInTheDocument();
    });
  });

  it('clears AI analysis when switching tasks', async () => {
    api.createReview.mockResolvedValue({ id: 'r1' });
    api.aiAnalyze.mockResolvedValue({
      analysis: {
        all_fixed: true,
        score: 10,
        detected_critical: 0,
        total_critical: 0,
        detected_medium: 0,
        total_medium: 0,
        detected_low: 0,
        total_low: 0,
        missed_issues: [],
        feedback: ['Perfect!'],
        summary: 'Done.',
        issues: [],
      },
    });

    const tasks = [
      { id: 'task-1', title: 'T1', language: 'python' },
      { id: 'task-2', title: 'T2', language: 'python' },
    ];
    vi.spyOn(Math, 'random').mockReturnValue(0.99);
    api.getTasks.mockResolvedValue(tasks);
    api.getTaskById
      .mockResolvedValueOnce(fullTask)
      .mockResolvedValueOnce({ ...fullTask, id: 'task-2', title: 'T2' });

    render(<App />);
    await waitFor(() => expect(screen.getByText('Validate Input')).toBeInTheDocument());

    // Submit and get analysis
    await userEvent.click(screen.getByText('Submit Review'));
    await waitFor(() => expect(screen.getByText('✓ All issues addressed')).toBeInTheDocument());

    // Switch task — analysis should disappear
    await userEvent.click(screen.getByText('Next Task'));
    await waitFor(() => {
      expect(screen.queryByText('✓ All issues addressed')).not.toBeInTheDocument();
    });

    Math.random.mockRestore();
  });

  it('toggles reference and edits comment via CodeReviewPanel callbacks', async () => {
    const taskWithRefs = {
      ...fullTask,
      code: 'line1\nline2',
      reference_issues: [
        { id: 'r1', line: 1, title: 'Issue', severity: 'critical', description: 'Desc' },
      ],
    };
    api.getTaskById.mockResolvedValue(taskWithRefs);

    render(<App />);
    await waitFor(() => expect(screen.getByText('Validate Input')).toBeInTheDocument());

    // Toggle reference on
    await userEvent.click(screen.getByText('Show Answer'));
    expect(screen.getByText('Hide Answer')).toBeInTheDocument();

    // Toggle reference off
    await userEvent.click(screen.getByText('Hide Answer'));
    expect(screen.getByText('Show Answer')).toBeInTheDocument();
  });

  it('clicking Python button when already on Python is a no-op', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python'));

    // Click Python again
    await userEvent.click(screen.getByText('Python'));
    // The language is already 'python', React won't re-trigger the effect
    // Just check the button has active class
    expect(screen.getByText('Python').className).toContain('lang-active');
  });

  it('adds and edits inline comments', async () => {
    api.getTaskById.mockResolvedValue({
      ...fullTask,
      code: 'line1\nline2\nline3',
    });

    render(<App />);
    await waitFor(() => expect(screen.getByText('Validate Input')).toBeInTheDocument());

    // Select line 1 and add a comment
    const line1 = screen.getByText('1');
    fireEvent.mouseDown(line1);
    fireEvent.mouseUp(line1.closest('.code-scroll') || document);

    const [commentArea, suggestionArea] = screen.getAllByRole('textbox');
    await userEvent.type(commentArea, 'Found a bug');
    await userEvent.type(suggestionArea, 'Fix the bug');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(screen.getByText('Found a bug')).toBeInTheDocument();

    // Edit the comment
    await userEvent.click(screen.getByText('Edit'));
    const editAreas = screen.getAllByRole('textbox');
    await userEvent.clear(editAreas[0]);
    await userEvent.type(editAreas[0], 'Updated bug');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(screen.getByText('Updated bug')).toBeInTheDocument();
  });
});
