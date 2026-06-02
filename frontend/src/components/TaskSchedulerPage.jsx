import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import LeftPanel from './LeftPanel';
import CodeReviewPanel from './CodeReviewPanel';

function formatMeta(task) {
  return task.language.replaceAll('_', ' ');
}

function formatComplexity(value = '') {
  if (!value) return '';

  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function getOverallCompleteness(ai) {
  if (!ai) return null;

  const totalIssues = ai.total_critical + ai.total_medium + ai.total_low;
  const detectedIssues = ai.detected_critical + ai.detected_medium + ai.detected_low;

  if (!totalIssues) {
    return ai.all_fixed ? 100 : 0;
  }

  return Math.round((detectedIssues / totalIssues) * 100);
}

export default function TaskSchedulerPage({ currentUser, onError }) {
  const [interests, setInterests] = useState([]);
  const [scheduledTasks, setScheduledTasks] = useState([]);
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [answer, setAnswer] = useState('');
  const [taskResults, setTaskResults] = useState({});
  const [aiLoading, setAiLoading] = useState(false);
  const [showReference, setShowReference] = useState(false);
  const [loading, setLoading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const loadSchedule = useCallback(
    async ({ regenerate = false } = {}) => {
      if (!currentUser) {
        setInterests([]);
        setScheduledTasks([]);
        setSelectedTaskId(null);
        return;
      }

      try {
        if (regenerate) {
          setRegenerating(true);
        } else {
          setLoading(true);
        }
        onError('');
        const [interestsResponse, scheduleResponse] = await Promise.all([
          api.getUserInterests(),
          regenerate ? api.regenerateTaskSchedule() : api.getTaskSchedule(),
        ]);

        setInterests(interestsResponse.interests || []);
        setScheduledTasks(scheduleResponse.tasks || []);
        setSelectedTaskId((previousId) => {
          if (previousId && scheduleResponse.tasks?.some((entry) => entry.id === previousId)) {
            return previousId;
          }

          return scheduleResponse.tasks?.[0]?.id ?? null;
        });
        setComments([]);
        setAnswer('');
        setTaskResults({});
        setShowReference(false);
      } catch (error) {
        onError(error.message || 'Failed to load task schedule');
      } finally {
        setLoading(false);
        setRegenerating(false);
      }
    },
    [currentUser, onError],
  );

  useEffect(() => {
    loadSchedule();
  }, [loadSchedule]);

  useEffect(() => {
    let active = true;

    async function loadTask() {
      if (!selectedTaskId) {
        setTask(null);
        return;
      }

      try {
        const fullTask = await api.getTaskById(selectedTaskId);
        if (!active) return;
        setTask(fullTask);
      } catch (error) {
        if (!active) return;
        onError(error.message || 'Failed to load scheduled task');
      }
    }

    loadTask();

    return () => {
      active = false;
    };
  }, [selectedTaskId, onError]);

  const selectedSummary = useMemo(
    () => scheduledTasks.find((entry) => entry.id === selectedTaskId) || null,
    [scheduledTasks, selectedTaskId],
  );
  const selectedAiAnalysis = selectedTaskId ? taskResults[selectedTaskId] || null : null;

  async function submitReview() {
    if (!task) return;

    try {
      setAiLoading(true);
      onError('');
      const review = await api.createReview({
        task_id: task.id,
        comments,
        answer,
      });
      const result = await api.aiAnalyze({ review_id: review.id });
      setTaskResults((previous) => ({
        ...previous,
        [task.id]: result,
      }));
    } catch (error) {
      setTaskResults((previous) => ({
        ...previous,
        [task.id]: { error: true },
      }));
      onError(error.message || 'Failed to analyze scheduled task review');
    } finally {
      setAiLoading(false);
    }
  }

  if (!currentUser) {
    return (
      <section className="task-scheduler-empty card reveal">
        <p className="eyebrow">Task Scheduler</p>
        <h2>Sign in to get your scheduled tasks</h2>
        <p className="muted">
          The scheduler builds a random daily queue from your saved interests and skips anything you
          already completed.
        </p>
      </section>
    );
  }

  if (!interests.length && !loading) {
    return (
      <section className="task-scheduler-empty card reveal">
        <p className="eyebrow">Task Scheduler</p>
        <h2>Pick interests before scheduling tasks</h2>
        <p className="muted">
          Save at least one category on the User Interests page so the scheduler can assign tasks.
        </p>
      </section>
    );
  }

  return (
    <section className="task-scheduler-layout">
      <aside className="task-scheduler-menu card reveal">
        <div className="task-scheduler-header">
          <p className="eyebrow">Today&apos;s Tasks</p>
        </div>
        <div className="task-scheduler-actions">
          <button
            type="button"
            onClick={() => loadSchedule({ regenerate: true })}
            disabled={loading || regenerating}
          >
            {regenerating ? 'Regenerating...' : 'Regenerate Tasks'}
          </button>
        </div>
        {loading ? <p className="muted">Loading tasks...</p> : null}
        {!loading && !scheduledTasks.length ? (
          <p className="muted">No remaining tasks match your interests right now.</p>
        ) : null}
        <div className="task-progress-list">
          {scheduledTasks.map((entry) => {
            const isActive = entry.id === selectedSummary?.id;
            const taskResult = taskResults[entry.id]?.analysis;
            const taskCompleteness = getOverallCompleteness(taskResult);
            const isAnalyzingCurrentTask = aiLoading && entry.id === selectedTaskId;
            return (
              <button
                key={entry.id}
                type="button"
                className={`task-progress-item${isActive ? ' task-progress-item-active' : ''}`}
                onClick={() => {
                  setSelectedTaskId(entry.id);
                  setComments([]);
                  setAnswer('');
                  setShowReference(false);
                }}
              >
                <span className="task-progress-item-title">{entry.title}</span>
                <span className="task-scheduler-item-summary">
                  <span className="task-progress-item-meta">{formatMeta(entry)}</span>
                  {entry.complexity ? (
                    <span
                      className={`task-complexity-badge task-scheduler-item-complexity task-complexity-${entry.complexity}`}
                    >
                      {formatComplexity(entry.complexity)}
                    </span>
                  ) : null}

                  {entry.is_completed ? (
                    <span className="task-completed-badge task-scheduler-item-complexity">
                      Completed
                    </span>
                  ) : null}
                </span>
                {taskResult ? (
                  <span className="task-scheduler-item-progress">
                    <span>Score: {taskResult.score} / 10</span>
                    <span>Progress: {taskCompleteness}%</span>
                  </span>
                ) : null}
                {isAnalyzingCurrentTask ? (
                  <span className="task-scheduler-item-progress task-scheduler-item-progress-pending">
                    <span>Analyzing...</span>
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      </aside>

      <div className="task-scheduler-detail layout-grid">
        <LeftPanel task={task} aiAnalysis={selectedAiAnalysis} aiLoading={aiLoading} />
        <CodeReviewPanel
          isCompleted={task?.is_completed}
          code={task?.code || ''}
          language={task?.language || 'python'}
          instructions={task?.instructions || []}
          responseMode={task?.submission_mode || 'comments'}
          comments={comments}
          answer={answer}
          answerEditorKey={task?.id || 'scheduled-task-answer'}
          referenceIssues={showReference ? task?.reference_issues || [] : []}
          referenceIssueCount={task?.reference_issues?.length || 0}
          showReference={showReference}
          onToggleReference={() => setShowReference((value) => !value)}
          onAddComment={(comment) => setComments((previous) => [...previous, comment])}
          onEditComment={(index, updated) =>
            setComments((previous) =>
              previous.map((comment, currentIndex) => (currentIndex === index ? updated : comment)),
            )
          }
          onAnswerChange={setAnswer}
          onSubmitReview={submitReview}
        />
      </div>
    </section>
  );
}
