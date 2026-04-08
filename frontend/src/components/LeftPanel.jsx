import React from 'react';

export default function LeftPanel({ task, evaluation }) {
  if (!task) {
    return <aside className="left-panel card">Loading task...</aside>;
  }

  const e = evaluation?.evaluation;

  return (
    <aside className="left-panel card reveal">
      <section>
        <p className="eyebrow">PR Title</p>
        <h2>{task.title}</h2>
        <p className="muted">{task.description}</p>
      </section>

      <section>
        <p className="eyebrow">Requirements</p>
        <ul>
          {task.requirements.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      {e ? (
        <section className="eval-section">
          <p className="eyebrow">Evaluation</p>
          <p className="score">Score: {e.score} / 10</p>
          <p className="eval-stats">
            Critical: {e.detected_critical}/{e.total_critical} &middot; Medium: {e.detected_medium}/{e.total_medium} &middot; Low: {e.detected_low}/{e.total_low}
          </p>
          {e.missed_issue_ids.length ? (
            <p className="eval-missed">Missed: {e.missed_issue_ids.join(', ')}</p>
          ) : null}
          <ul className="eval-feedback">
            {e.feedback.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </aside>
  );
}
