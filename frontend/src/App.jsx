import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import LeftPanel from './components/LeftPanel';
import CodeReviewPanel from './components/CodeReviewPanel';
import EvaluationCard from './components/EvaluationCard';

export default function App() {
  const [taskList, setTaskList] = useState([]);
  const [taskIndex, setTaskIndex] = useState(0);
  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [reviewerName, setReviewerName] = useState('');
  const [evaluation, setEvaluation] = useState(null);
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
    setEvaluation(null);
  }

  async function submitReview() {
    if (!task || !comments.length || !reviewerName.trim()) return;

    try {
      setError('');
      const review = await api.createReview({
        task_id: task.id,
        reviewer_name: reviewerName,
        comments,
      });

      const result = await api.evaluate({ review_id: review.id });
      setEvaluation(result);
    } catch (e) {
      setError(e.message || 'Failed to evaluate review');
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar reveal">
        <h1>PR Review Trainer</h1>
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
        <LeftPanel task={task} />
        <CodeReviewPanel
          code={task?.code || ''}
          language={task?.language || 'python'}
          comments={comments}
          onAddComment={(c) => setComments((prev) => [...prev, c])}
          onSubmitReview={submitReview}
          reviewerName={reviewerName}
          setReviewerName={setReviewerName}
        />
      </section>

      <EvaluationCard data={evaluation} />
    </main>
  );
}
