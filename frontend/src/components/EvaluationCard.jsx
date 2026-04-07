import React from 'react';

export default function EvaluationCard({ data }) {
  if (!data) return null;

  const e = data.evaluation;
  return (
    <section className="eval-card card reveal">
      <h3>AI Evaluation</h3>
      <p className="score">Score: {e.score} / 10</p>
      <p>
        Critical: {e.detected_critical}/{e.total_critical} | Medium: {e.detected_medium}/{e.total_medium} |
        Low: {e.detected_low}/{e.total_low}
      </p>
      <p>Missed issues: {e.missed_issue_ids.length ? e.missed_issue_ids.join(', ') : 'None'}</p>
      <ul>
        {e.feedback.map((f) => (
          <li key={f}>{f}</li>
        ))}
      </ul>
    </section>
  );
}
