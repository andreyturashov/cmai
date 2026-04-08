import React, { useState } from 'react';

export default function CommentForm({ line, onSave, onCancel }) {
  const [comment, setComment] = useState('');
  const [suggestion, setSuggestion] = useState('');

  function submit(e) {
    e.preventDefault();
    if (!comment.trim() || !suggestion.trim()) return;

    onSave({
      line,
      comment: comment.trim(),
      suggestion: suggestion.trim(),
    });
  }

  return (
    <form className="comment-form" onSubmit={submit}>
      <div className="comment-meta">Line {line}</div>
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
