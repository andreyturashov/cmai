import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the api module
vi.mock('./api/client', () => ({
  api: {
    getAuthSession: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout: vi.fn(),
    getTasks: vi.fn(),
    getTaskById: vi.fn(),
    getUserProgress: vi.fn(),
    getUserInterests: vi.fn(),
    updateUserInterests: vi.fn(),
    createReview: vi.fn(),
    aiAnalyze: vi.fn(),
  },
}));

vi.mock('@react-oauth/google', () => ({
  GoogleOAuthProvider: ({ children }) => <>{children}</>,
  GoogleLogin: ({ onSuccess, onError }) => (
    <div>
      <button onClick={() => onSuccess?.({ credential: 'google-test-token' })}>
        Sign in with Google
      </button>
      <button onClick={() => onError?.()}>Trigger Google Error</button>
    </div>
  ),
}));

vi.mock('./components/RichAnswerEditor', () => ({
  default: function MockRichAnswerEditor({ value = '', onChange, ariaLabel = 'Your Answer' }) {
    return (
      <textarea
        aria-label={ariaLabel}
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
      />
    );
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
    window.history.replaceState({}, '', '/');
    api.getAuthSession.mockResolvedValue({ user: null });
    api.loginWithGoogle.mockResolvedValue({
      user: {
        id: 1,
        email: 'user@example.com',
        name: 'Example User',
        avatar_url: '',
      },
    });
    api.logout.mockResolvedValue({ user: null });
    api.getTasks.mockResolvedValue([taskSummary]);
    api.getTaskById.mockResolvedValue(fullTask);
    api.getUserProgress.mockResolvedValue([]);
    api.getUserInterests.mockResolvedValue({ interests: [] });
    api.updateUserInterests.mockResolvedValue({ interests: [] });
  });

  it('renders the header', async () => {
    render(<App />);
    expect(screen.getByText('Code Mentor')).toBeInTheDocument();
    await waitFor(() => expect(api.getTasks).toHaveBeenCalled());
  });

  it('shows Google login without blocking the main page', async () => {
    render(<App />);
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Validate Input')).toBeInTheDocument());
  });

  it('logs in with Google and shows the signed-in user', async () => {
    render(<App />);
    await userEvent.click(screen.getByText('Sign in with Google'));

    await waitFor(() =>
      expect(api.loginWithGoogle).toHaveBeenCalledWith({ credential: 'google-test-token' }),
    );
    await waitFor(() => expect(screen.getByText('Example User')).toBeInTheDocument());
  });

  it('logs out the signed-in user', async () => {
    api.getAuthSession.mockResolvedValue({
      user: {
        id: 1,
        email: 'user@example.com',
        name: 'Example User',
        avatar_url: '',
      },
    });

    render(<App />);
    await waitFor(() => expect(screen.getByText('Example User')).toBeInTheDocument());

    await userEvent.click(screen.getByText('Log out'));
    await waitFor(() => expect(api.logout).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText('Sign in with Google')).toBeInTheDocument());
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
    expect(screen.getByText('FastAPI')).toBeInTheDocument();
    expect(screen.getByText('Django')).toBeInTheDocument();
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
    expect(screen.getByText('User Interests')).toBeInTheDocument();
    await waitFor(() => expect(api.getTasks).toHaveBeenCalled());
  });

  it('navigates to User Interests and saves up to five interests', async () => {
    api.getAuthSession.mockResolvedValue({
      user: {
        id: 1,
        email: 'user@example.com',
        name: 'Example User',
        avatar_url: '',
      },
    });
    api.getUserInterests.mockResolvedValue({ interests: ['python_theory', 'javascript'] });
    api.updateUserInterests.mockResolvedValue({
      interests: ['python_theory', 'javascript', 'fastapi', 'django', 'react'],
    });

    render(<App />);
    await userEvent.click(screen.getByText('User Interests'));

    await waitFor(() => expect(api.getUserInterests).toHaveBeenCalled());
    await waitFor(() =>
      expect(screen.getByText('Choose up to 5 categories to learn')).toBeInTheDocument(),
    );

    await userEvent.click(screen.getByRole('button', { name: 'FastAPI' }));
    await userEvent.click(screen.getByRole('button', { name: 'Django' }));
    await userEvent.click(screen.getByRole('button', { name: 'React' }));

    expect(screen.getByRole('button', { name: 'Python' })).toBeDisabled();

    await userEvent.click(screen.getByRole('button', { name: 'Save Interests' }));

    await waitFor(() =>
      expect(api.updateUserInterests).toHaveBeenCalledWith({
        interests: ['python_theory', 'javascript', 'fastapi', 'django', 'react'],
      }),
    );
    await waitFor(() => expect(screen.getByText('Saved')).toBeInTheDocument());
    expect(window.location.pathname).toBe('/user-interests');
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

  it('switches to FastAPI language', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python'));

    api.getTasks.mockResolvedValue([
      { id: 'fastapi-task-1', title: 'Create account endpoint', language: 'fastapi' },
    ]);
    api.getTaskById.mockResolvedValue({
      ...fullTask,
      id: 'fastapi-task-1',
      title: 'Create account endpoint',
      language: 'fastapi',
    });

    await userEvent.click(screen.getByText('FastAPI'));
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('fastapi'));
  });

  it('switches to Django language', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python'));

    api.getTasks.mockResolvedValue([
      { id: 'django-task-1', title: 'Create article view', language: 'django' },
    ]);
    api.getTaskById.mockResolvedValue({
      ...fullTask,
      id: 'django-task-1',
      title: 'Create article view',
      language: 'django',
    });

    await userEvent.click(screen.getByText('Django'));
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('django'));
  });

  it('switches to React language', async () => {
    render(<App />);
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('python'));

    api.getTasks.mockResolvedValue([
      { id: 'react-task-1', title: 'Add todo item', language: 'react' },
    ]);
    api.getTaskById.mockResolvedValue({
      ...fullTask,
      id: 'react-task-1',
      title: 'Add todo item',
      language: 'react',
    });

    await userEvent.click(screen.getByText('React'));
    await waitFor(() => expect(api.getTasks).toHaveBeenCalledWith('react'));
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
      screen.getByRole('textbox', { name: 'Your Answer' }),
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

  it('navigates to TaskProgress and loads saved progress', async () => {
    api.getAuthSession.mockResolvedValue({
      user: {
        id: 1,
        email: 'user@example.com',
        name: 'Example User',
        avatar_url: '',
      },
    });
    api.getUserProgress.mockResolvedValue([
      {
        id: 101,
        task_id: 'task-1',
        score: 8.5,
        suggestion: 'Strong answer. Expand on tradeoffs next time.',
        ai_analysis: {
          all_fixed: false,
          score: 8.5,
          detected_critical: 0,
          total_critical: 0,
          detected_medium: 1,
          total_medium: 2,
          detected_low: 1,
          total_low: 1,
          missed_issues: ['Missing edge-case handling'],
          feedback: ['Good structure', 'Add explicit validation'],
          issues: [
            {
              issue_id: 'issue-1',
              title: 'Missing edge-case handling',
              severity: 'medium',
              addressed: false,
              explanation: 'The review did not mention absent env vars.',
            },
          ],
          summary: 'Some important configuration checks are still missing.',
        },
        user_answer: 'Lists are mutable while tuples are immutable.',
        user_comments: [
          {
            line: 2,
            end_line: null,
            severity: 'medium',
            comment: 'Guard against writing raw arrays directly.',
            suggestion: 'Join the ids before writing them.',
          },
        ],
        submission_count: 2,
        created_at: '2026-05-20T10:00:00Z',
        updated_at: '2026-05-20T11:00:00Z',
        task: {
          ...fullTask,
          submission_mode: 'answer',
          reference_issues: [
            {
              id: 'issue-1',
              line: 1,
              severity: 'medium',
              title: 'Expected answer',
              description: 'Explain mutability.',
              suggestion: 'Mention immutable tuples.',
              code: 'Tuples are immutable.',
            },
          ],
        },
      },
    ]);

    render(<App />);
    await userEvent.click(screen.getByText('TaskProgress'));

    await waitFor(() => expect(api.getUserProgress).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText('Completed Tasks')).toBeInTheDocument());
    expect(screen.getAllByText('Score: 8.5 / 10')).toHaveLength(2);
    expect(screen.getByText('✗ Some issues remain')).toBeInTheDocument();
    expect(screen.getByText('Good structure')).toBeInTheDocument();
    expect(
      screen.getByText('Some important configuration checks are still missing.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Missing edge-case handling')).toBeInTheDocument();
    expect(screen.getByText('Lists are mutable while tuples are immutable.')).toBeInTheDocument();
    expect(screen.getByText('Guard against writing raw arrays directly.')).toBeInTheDocument();
    expect(screen.getByText('Suggestion: Join the ids before writing them.')).toBeInTheDocument();
    expect(window.location.pathname).toBe('/task-progress');
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

    const commentArea = screen.getByRole('textbox', { name: 'Comment' });
    await userEvent.type(commentArea, 'Found a bug');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(screen.getByText('Found a bug')).toBeInTheDocument();

    // Edit the comment
    await userEvent.click(screen.getByText('Edit'));
    const editArea = screen.getByRole('textbox', { name: 'Comment' });
    await userEvent.clear(editArea);
    await userEvent.type(editArea, 'Updated bug');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(screen.getByText('Updated bug')).toBeInTheDocument();
  });
});
