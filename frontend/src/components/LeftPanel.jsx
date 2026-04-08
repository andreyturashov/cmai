import React from 'react';

export default function LeftPanel({ task, aiAnalysis, aiLoading }) {
  if (!task) {
    return <aside className="left-panel card">Loading task...</aside>;
  }

  const ai = aiAnalysis?.analysis;
  const aiError = aiAnalysis?.error;

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

      {aiLoading ? (
        <section className="ai-section">
          <p className="eyebrow">AI Analysis</p>
          <div className="ai-loading">
            <span className="ai-spinner" />
            Analyzing with Ollama&hellip;
          </div>
        </section>
      ) : aiError ? (
        <section className="ai-section">
          <p className="eyebrow">AI Analysis</p>
          <p className="ai-error">AI analysis unavailable</p>
        </section>
      ) : ai ? (
        <section className="eval-section">
          <p className="eyebrow">AI Analysis</p>
          <div className={`ai-badge ${ai.all_fixed ? 'ai-badge-pass' : 'ai-badge-fail'}`}>
            {ai.all_fixed ? '✓ All issues addressed' : '✗ Some issues remain'}
          </div>
          <p className="score">Score: {ai.score} / 10</p>
          <p className="eval-stats">
            Critical: {ai.detected_critical}/{ai.total_critical} &middot; Medium: {ai.detected_medium}/{ai.total_medium} &middot; Low: {ai.detected_low}/{ai.total_low}
          </p>
          {ai.missed_issues.length ? (
            <p className="eval-missed">Missed: {ai.missed_issues.join(', ')}</p>
          ) : null}
          <ul className="eval-feedback">
            {ai.feedback.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          <p className="ai-summary">{ai.summary}</p>
          <ul className="ai-verdicts">
            {ai.issues.map((v) => (
              <li key={v.issue_id} className={v.addressed ? 'ai-ok' : 'ai-miss'}>
                <span className="ai-verdict-icon">{v.addressed ? '✓' : '✗'}</span>
                <span>
                  <strong>{v.title || v.issue_id}</strong>
                  {v.severity ? <span className={`verdict-severity sev-${v.severity}`}> ({v.severity})</span> : null}
                  <br />
                  {v.explanation}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </aside>
  );
}
