import React, { useState } from 'react';

export default function CommentForm({ line, endLine, onSave, onCancel, initial }) {
  const [comment, setComment] = useState(initial?.comment || '');
  const [suggestion, setSuggestion] = useState(initial?.suggestion || '');

  function submit(e) {
    e.preventDefault();
    if (!comment.trim() || !suggestion.trim()) return;

    onSave({
      line,
      ...(endLine ? { end_line: endLine } : {}),
      comment: comment.trim(),
      suggestion: suggestion.trim(),
    });
  }

  const label = endLine ? `Lines ${line}–${endLine}` : `Line ${line}`;

  return (
    <form className="comment-form" onSubmit={submit}>
      <div className="comment-meta">{label}</div>
      <label>
        Comment
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          placeholder="Describe the issue and why it matters"
          required
        />
      </label>
      <label>
        Suggestion
        <textarea
          value={suggestion}
          onChange={(e) => setSuggestion(e.target.value)}
          rows={3}
          placeholder="Propose a fix"
          required
        />
      </label>
      <div className="actions">
        <button type="button" className="ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit">Save Comment</button>
      </div>
    </form>
  );
}
