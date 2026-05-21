import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import AuthControls from './components/AuthControls';
import LeftPanel from './components/LeftPanel';
import CodeReviewPanel from './components/CodeReviewPanel';
import TaskProgressPage from './components/TaskProgressPage';
import TaskSchedulerPage from './components/TaskSchedulerPage';
import UserInterestsPage from './components/UserInterestsPage';
import { LANGUAGE_OPTIONS } from './constants/languageOptions';

const LANDING_PATH = '/';
const REVIEW_PATH = '/review';
const TASK_PROGRESS_PATH = '/task-progress';
const TASK_SCHEDULER_PATH = '/task-scheduler';
const USER_INTERESTS_PATH = '/user-interests';

const LANDING_FEATURES = [
  {
    title: 'Review like it matters',
    description:
      'Open realistic pull request tasks, leave inline comments by severity, and explain the engineering tradeoff behind every call.',
  },
  {
    title: 'Measure judgment, not just syntax',
    description:
      'Compare your review against reference issues and AI analysis so the feedback loop stays focused on code quality and risk.',
  },
  {
    title: 'Build a durable practice rhythm',
    description:
      'Track progress over time, set up scheduled task queues, and tune the practice mix around your interests and stack.',
  },
];

const LANDING_EXAMPLE = {
  taskTitle: 'Secure avatar uploads',
  requirementLines: [
    'Identify the security issue',
    'Explain the user impact',
    'Recommend a safer implementation',
  ],
  score: '7 / 10',
  analysisGood:
    'You correctly flagged the filename handling risk and suggested generating a safe server-side name.',
  analysisMissing:
    'You did not mention that the code writes any uploaded file to disk without validating file type or size first.',
  analysisGoodBadge: 'GOOD CATCH',
  analysisMissingBadge: 'MISSED',
  codeLines: [
    'def save_avatar(file_bytes, filename):',
    '    destination = f"/srv/app/uploads/{filename}"',
    '    with open(destination, "wb") as target:',
    '        target.write(file_bytes)',
    '    return destination',
    '',
    'avatar_path = save_avatar(payload, upload.name)',
  ],
  comment:
    'Use a generated filename here instead of raw user input, otherwise ../ segments can escape the uploads directory.',
};

function getCurrentPath() {
  if (typeof window === 'undefined') return LANDING_PATH;
  if (window.location.pathname === REVIEW_PATH) return REVIEW_PATH;
  if (window.location.pathname === TASK_PROGRESS_PATH) return TASK_PROGRESS_PATH;
  if (window.location.pathname === TASK_SCHEDULER_PATH) return TASK_SCHEDULER_PATH;
  if (window.location.pathname === USER_INTERESTS_PATH) return USER_INTERESTS_PATH;
  return LANDING_PATH;
}

export default function App() {
  const [path, setPath] = useState(getCurrentPath);
  const [taskList, setTaskList] = useState([]);
  const [taskIndex, setTaskIndex] = useState(0);
  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [answer, setAnswer] = useState('');
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [showReference, setShowReference] = useState(false);
  const [error, setError] = useState('');
  const [language, setLanguage] = useState('python');
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);

  useEffect(() => {
    function handlePopState() {
      setPath(getCurrentPath());
    }

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  useEffect(() => {
    async function loadAuthSession() {
      try {
        const session = await api.getAuthSession();
        setCurrentUser(session.user || null);
      } catch {
        setCurrentUser(null);
      }
    }

    loadAuthSession();
  }, []);

  useEffect(() => {
    async function loadTasks() {
      if (path !== REVIEW_PATH) return;

      try {
        setError('');
        const tasks = await api.getTasks(language);
        // Shuffle tasks randomly
        for (let i = tasks.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [tasks[i], tasks[j]] = [tasks[j], tasks[i]];
        }
        setTaskList(tasks);
        setTaskIndex(0);
        setComments([]);
        setAnswer('');
        setAiAnalysis(null);
        setShowReference(false);
      } catch (e) {
        setError(e.message || 'Failed to load task');
      }
    }

    loadTasks();
  }, [language, path]);

  useEffect(() => {
    if (path !== REVIEW_PATH) return;

    async function loadSelectedTask() {
      if (!taskList.length) {
        setTask(null);
        return;
      }

      try {
        setError('');
        const selected = taskList[taskIndex];
        const fullTask = await api.getTaskById(selected.id);
        setTask(fullTask);
      } catch (e) {
        setError(e.message || 'Failed to load task');
      }
    }

    loadSelectedTask();
  }, [taskList, taskIndex, path]);

  function moveTask(nextIndex) {
    if (!taskList.length) return;

    const boundedIndex = nextIndex >= taskList.length ? 0 : nextIndex;
    setTaskIndex(boundedIndex);
    setComments([]);
    setAnswer('');
    setAiAnalysis(null);
    setShowReference(false);
  }

  async function submitReview() {
    if (!task) return;

    try {
      setError('');
      const review = await api.createReview({
        task_id: task.id,
        comments,
        answer,
      });

      setAiLoading(true);
      setAiAnalysis(null);
      const res = await api.aiAnalyze({ review_id: review.id });
      setAiAnalysis(res);
    } catch (e) {
      setAiAnalysis({ error: true });
      setError(e.message || 'Failed to analyze review');
    } finally {
      setAiLoading(false);
    }
  }

  async function handleGoogleLogin(credential) {
    try {
      setAuthLoading(true);
      setError('');
      const session = await api.loginWithGoogle({ credential });
      setCurrentUser(session.user || null);
    } catch (e) {
      setError(e.message || 'Failed to sign in with Google');
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogout() {
    try {
      setAuthLoading(true);
      setError('');
      const session = await api.logout();
      setCurrentUser(session.user || null);
    } catch (e) {
      setError(e.message || 'Failed to log out');
    } finally {
      setAuthLoading(false);
    }
  }

  function navigateTo(nextPath) {
    const normalizedPath =
      nextPath === LANDING_PATH
        ? LANDING_PATH
        : nextPath === REVIEW_PATH
          ? REVIEW_PATH
          : nextPath === TASK_PROGRESS_PATH
            ? TASK_PROGRESS_PATH
            : nextPath === TASK_SCHEDULER_PATH
              ? TASK_SCHEDULER_PATH
              : nextPath === USER_INTERESTS_PATH
                ? USER_INTERESTS_PATH
                : LANDING_PATH;
    if (normalizedPath === path) return;

    window.history.pushState({}, '', normalizedPath);
    setPath(normalizedPath);
    setError('');
  }

  const isLandingPage = path === LANDING_PATH;
  const isTaskProgressPage = path === TASK_PROGRESS_PATH;
  const isTaskSchedulerPage = path === TASK_SCHEDULER_PATH;
  const isUserInterestsPage = path === USER_INTERESTS_PATH;
  const isReviewPage = path === REVIEW_PATH;
  const currentYear = new Date().getFullYear();

  return (
    <main className="app-shell">
      <header className="topbar reveal">
        <div className="topbar-main-row">
          <div className="page-nav">
            <button
              type="button"
              className={isLandingPage ? 'page-nav-active' : 'ghost'}
              onClick={() => navigateTo(LANDING_PATH)}
            >
              Home
            </button>
            <button
              type="button"
              className={isReviewPage ? 'page-nav-active' : 'ghost'}
              onClick={() => navigateTo(REVIEW_PATH)}
            >
              Code Review
            </button>
            <button
              type="button"
              className={isTaskProgressPage ? 'page-nav-active' : 'ghost'}
              onClick={() => navigateTo(TASK_PROGRESS_PATH)}
            >
              Task Progress
            </button>
            <button
              type="button"
              className={isTaskSchedulerPage ? 'page-nav-active' : 'ghost'}
              onClick={() => navigateTo(TASK_SCHEDULER_PATH)}
            >
              Task Scheduler
            </button>
            <button
              type="button"
              className={isUserInterestsPage ? 'page-nav-active' : 'ghost'}
              onClick={() => navigateTo(USER_INTERESTS_PATH)}
            >
              User Interests
            </button>
          </div>
          <div className="topbar-auth">
            <AuthControls
              user={currentUser}
              loading={authLoading}
              onLogin={handleGoogleLogin}
              onLogout={handleLogout}
              onError={setError}
            />
          </div>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      {isTaskProgressPage ? (
        <TaskProgressPage currentUser={currentUser} onError={setError} />
      ) : isTaskSchedulerPage ? (
        <TaskSchedulerPage currentUser={currentUser} onError={setError} />
      ) : isUserInterestsPage ? (
        <UserInterestsPage currentUser={currentUser} onError={setError} />
      ) : isLandingPage ? (
        <div className="landing-page">
          <section className="hero-panel reveal">
            <div className="hero-copy">
              <p className="hero-kicker">PR review training for shipping engineers</p>
              <h2>Practice on realistic diffs before the stakes are real.</h2>
              <p className="hero-body">
                Code Mentor turns review practice into a structured loop: inspect code, leave
                comments with intent, use AI analysis to sharpen your feedback, compare your
                thinking to reference issues, and keep momentum with progress tracking and scheduled
                exercises.
              </p>
              <div className="hero-actions">
                <button type="button" onClick={() => navigateTo(REVIEW_PATH)}>
                  Start Reviewing
                </button>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => navigateTo(TASK_PROGRESS_PATH)}
                >
                  See Progress
                </button>
              </div>
            </div>

            <aside className="hero-signal card">
              <div className="hero-example-preview">
                <section className="hero-example-detail">
                  <p className="hero-example-section-label">PR Title</p>
                  <h4>{LANDING_EXAMPLE.taskTitle}</h4>
                  <div className="hero-example-detail-block">
                    <p className="hero-example-section-label">Requirements</p>
                    <ul>
                      {LANDING_EXAMPLE.requirementLines.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="hero-example-detail-block">
                    <p className="hero-example-section-label">AI Analysis</p>
                    <strong>Score: {LANDING_EXAMPLE.score}</strong>
                    <p className="hero-example-positive-note">
                      Good: {LANDING_EXAMPLE.analysisGood}{' '}
                      <span>({LANDING_EXAMPLE.analysisGoodBadge})</span>
                    </p>
                    <p className="hero-example-missing-note">
                      Missing: {LANDING_EXAMPLE.analysisMissing}{' '}
                      <span>({LANDING_EXAMPLE.analysisMissingBadge})</span>
                    </p>
                  </div>
                </section>

                <section className="hero-example-code">
                  <div className="hero-example-code-topbar">
                    <strong>TaskProgress Viewer</strong>
                  </div>
                  <div className="hero-example-code-window">
                    {LANDING_EXAMPLE.codeLines.map((line, index) => (
                      <div key={`${index + 1}-${line}`} className="hero-example-code-line">
                        <span>{index + 1}</span>
                        <code>{line || ' '}</code>
                      </div>
                    ))}
                    <div className="hero-example-comment-bubble">
                      <span>{LANDING_EXAMPLE.comment}</span>
                      <strong>Line 2</strong>
                    </div>
                  </div>
                </section>
              </div>
            </aside>
          </section>

          <section className="landing-grid reveal" aria-label="Product overview">
            {LANDING_FEATURES.map((feature) => (
              <article key={feature.title} className="card landing-card">
                <p className="eyebrow">Feature</p>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </article>
            ))}
          </section>

          <footer className="landing-footer reveal">
            <p>© {currentYear} Code Mentor. All rights reserved.</p>
          </footer>
        </div>
      ) : (
        <section className="review-workspace reveal">
          <div className="review-workspace-header">
            <div>
              <p className="eyebrow">Practice arena</p>
              <h3>Open a task and review it like a teammate would.</h3>
            </div>
            <div className="task-switcher">
              <div className="language-toggle">
                {LANGUAGE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    className={language === option.value ? 'lang-active' : ''}
                    onClick={() => setLanguage(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <button onClick={() => moveTask(taskIndex + 1)} disabled={!taskList.length}>
                Next Task
              </button>
            </div>
          </div>

          <div className="layout-grid">
            <LeftPanel task={task} aiAnalysis={aiAnalysis} aiLoading={aiLoading} />
            <CodeReviewPanel
              code={task?.code || ''}
              language={task?.language || 'python'}
              instructions={task?.instructions || []}
              responseMode={task?.submission_mode || 'comments'}
              comments={comments}
              answer={answer}
              answerEditorKey={task?.id || `${language}-${taskIndex}`}
              referenceIssues={showReference ? task?.reference_issues || [] : []}
              referenceIssueCount={task?.reference_issues?.length || 0}
              showReference={showReference}
              onToggleReference={() => setShowReference((v) => !v)}
              onAddComment={(c) => setComments((prev) => [...prev, c])}
              onEditComment={(idx, updated) =>
                setComments((prev) => prev.map((c, i) => (i === idx ? updated : c)))
              }
              onAnswerChange={setAnswer}
              onSubmitReview={submitReview}
            />
          </div>
        </section>
      )}
    </main>
  );
}
