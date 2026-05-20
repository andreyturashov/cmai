import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import LeftPanel from './LeftPanel';
import CodeReviewPanel from './CodeReviewPanel';

function formatMeta(entry) {
  const updatedAt = entry?.updated_at ? new Date(entry.updated_at) : null;
  const formattedDate =
    updatedAt && !Number.isNaN(updatedAt.getTime())
      ? new Intl.DateTimeFormat(undefined, {
          month: 'short',
          day: 'numeric',
        }).format(updatedAt)
      : 'No date';

  return `${entry.task.language} · ${entry.score}/10 · ${formattedDate}`;
}

export default function TaskProgressPage({ currentUser, onError }) {
  const [progressEntries, setProgressEntries] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showReference, setShowReference] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadProgress() {
      if (!currentUser) {
        setProgressEntries([]);
        setSelectedId(null);
        setShowReference(false);
        return;
      }

      try {
        setLoading(true);
        onError('');
        const entries = await api.getUserProgress();
        if (!active) return;
        setProgressEntries(entries);
        setSelectedId((previousId) => {
          if (previousId && entries.some((entry) => entry.id === previousId)) {
            return previousId;
          }

          return entries[0]?.id ?? null;
        });
        setShowReference(false);
      } catch (error) {
        if (!active) return;
        onError(error.message || 'Failed to load TaskProgress');
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadProgress();

    return () => {
      active = false;
    };
  }, [currentUser, onError]);

  const selectedEntry = useMemo(
    () => progressEntries.find((entry) => entry.id === selectedId) || null,
    [progressEntries, selectedId],
  );

  if (!currentUser) {
    return (
      <section className="task-progress-empty card reveal">
        <p className="eyebrow">TaskProgress</p>
        <h2>Sign in to view your completed tasks</h2>
        <p className="muted">
          Your saved submissions, scores, and answers appear here after you complete tasks while
          signed in.
        </p>
      </section>
    );
  }

  if (loading && !progressEntries.length) {
    return (
      <section className="task-progress-empty card reveal">
        <p className="eyebrow">TaskProgress</p>
        <h2>Loading your progress</h2>
      </section>
    );
  }

  if (!progressEntries.length) {
    return (
      <section className="task-progress-empty card reveal">
        <p className="eyebrow">TaskProgress</p>
        <h2>No completed tasks yet</h2>
        <p className="muted">Finish a task from the main review page and it will appear here.</p>
      </section>
    );
  }

  return (
    <section className="task-progress-layout">
      <aside className="task-progress-menu card reveal">
        <div className="task-progress-menu-header">
          <p className="eyebrow">TaskProgress</p>
          <h2>Completed Tasks</h2>
          <p className="muted">Review saved work, scores, and the original task details.</p>
        </div>
        <div className="task-progress-list">
          {progressEntries.map((entry) => {
            const isActive = entry.id === selectedEntry?.id;
            return (
              <button
                key={entry.id}
                type="button"
                className={`task-progress-item${isActive ? ' task-progress-item-active' : ''}`}
                onClick={() => {
                  setSelectedId(entry.id);
                  setShowReference(false);
                }}
              >
                <span className="task-progress-item-title">{entry.task.title}</span>
                <span className="task-progress-item-meta">{formatMeta(entry)}</span>
              </button>
            );
          })}
        </div>
      </aside>

      <div className="task-progress-detail layout-grid">
        <LeftPanel
          task={selectedEntry?.task}
          progressEntry={selectedEntry}
          aiAnalysis={selectedEntry?.ai_analysis ? { analysis: selectedEntry.ai_analysis } : null}
          aiLoading={false}
        />
        <CodeReviewPanel
          title="TaskProgress Viewer"
          code={selectedEntry?.task.code || ''}
          language={selectedEntry?.task.language || 'python'}
          instructions={selectedEntry?.task.instructions || []}
          responseMode={selectedEntry?.task.submission_mode || 'comments'}
          comments={selectedEntry?.user_comments || []}
          answer={selectedEntry?.user_answer || ''}
          savedAnswer={selectedEntry?.user_answer || ''}
          referenceIssues={showReference ? selectedEntry?.task.reference_issues || [] : []}
          referenceIssueCount={selectedEntry?.task.reference_issues?.length || 0}
          showReference={showReference}
          onToggleReference={() => setShowReference((value) => !value)}
          onAddComment={() => {}}
          onEditComment={() => {}}
          onAnswerChange={() => {}}
          onSubmitReview={() => {}}
          readOnly
        />
      </div>
    </section>
  );
}
