import React from 'react';

export default function LeftPanel({ task }) {
  if (!task) {
    return <aside className="left-panel card">Loading task...</aside>;
  }

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

      <section>
        <p className="eyebrow">Instructions</p>
        <ol>
          {task.instructions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>
    </aside>
  );
}
