import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import LeftPanel from './components/LeftPanel';
import CodeReviewPanel from './components/CodeReviewPanel';

export default function App() {
  const [taskList, setTaskList] = useState([]);
  const [taskIndex, setTaskIndex] = useState(0);
  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [showReference, setShowReference] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadTasks() {
      try {
        setError('');
        const tasks = await api.getTasks();
        setTaskList(tasks);
        setTaskIndex(0);
      } catch (e) {
        setError(e.message || 'Failed to load task');
      }
    }

    loadTasks();
  }, []);

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

    const boundedIndex = Math.max(0, Math.min(nextIndex, taskList.length - 1));
    setTaskIndex(boundedIndex);
    setComments([]);
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

  return (
    <main className="app-shell">
      <header className="topbar reveal">
        <h1>Code Mentor</h1>
        <p>Train your engineering judgment with realistic pull request reviews.</p>
        <div className="task-switcher">
          <button className="ghost" onClick={() => moveTask(taskIndex - 1)} disabled={taskIndex === 0}>
            Previous
          </button>
          <button
            onClick={() => moveTask(taskIndex + 1)}
            disabled={taskIndex === taskList.length - 1 || !taskList.length}
          >
            Next
          </button>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="layout-grid">
        <LeftPanel task={task} aiAnalysis={aiAnalysis} aiLoading={aiLoading} />
        <CodeReviewPanel
          code={task?.code || ''}
          language={task?.language || 'python'}
          comments={comments}
          referenceIssues={showReference ? task?.reference_issues || [] : []}
          showReference={showReference}
          onToggleReference={() => setShowReference((v) => !v)}
          onAddComment={(c) => setComments((prev) => [...prev, c])}
          onEditComment={(idx, updated) =>
            setComments((prev) => prev.map((c, i) => (i === idx ? updated : c)))
          }
          onSubmitReview={submitReview}
        />
      </section>
    </main>
  );
}
