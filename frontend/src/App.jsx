import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import AuthControls from './components/AuthControls';
import LeftPanel from './components/LeftPanel';
import CodeReviewPanel from './components/CodeReviewPanel';
import TaskProgressPage from './components/TaskProgressPage';
import UserInterestsPage from './components/UserInterestsPage';
import { LANGUAGE_OPTIONS } from './constants/languageOptions';

const REVIEW_PATH = '/';
const TASK_PROGRESS_PATH = '/task-progress';
const USER_INTERESTS_PATH = '/user-interests';

function getCurrentPath() {
  if (typeof window === 'undefined') return REVIEW_PATH;
  if (window.location.pathname === TASK_PROGRESS_PATH) return TASK_PROGRESS_PATH;
  if (window.location.pathname === USER_INTERESTS_PATH) return USER_INTERESTS_PATH;
  return REVIEW_PATH;
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
  }, [language]);

  useEffect(() => {
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
  }, [taskList, taskIndex]);

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
      nextPath === TASK_PROGRESS_PATH
        ? TASK_PROGRESS_PATH
        : nextPath === USER_INTERESTS_PATH
          ? USER_INTERESTS_PATH
          : REVIEW_PATH;
    if (normalizedPath === path) return;

    window.history.pushState({}, '', normalizedPath);
    setPath(normalizedPath);
    setError('');
  }

  const isTaskProgressPage = path === TASK_PROGRESS_PATH;
  const isUserInterestsPage = path === USER_INTERESTS_PATH;
  const isReviewPage = path === REVIEW_PATH;

  return (
    <main className="app-shell">
      <header className="topbar reveal">
        <h1>Code Mentor</h1>
        <p>Train your engineering judgment with realistic pull request reviews.</p>
        <div className="page-nav">
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
            TaskProgress
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
        {isReviewPage ? (
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
        ) : null}
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      {isTaskProgressPage ? (
        <TaskProgressPage currentUser={currentUser} onError={setError} />
      ) : isUserInterestsPage ? (
        <UserInterestsPage currentUser={currentUser} onError={setError} />
      ) : (
        <section className="layout-grid">
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
        </section>
      )}
    </main>
  );
}
