import React, { useState } from 'react';
import RichAnswerEditor from './RichAnswerEditor';

export default function CommentForm({ line, endLine, onSave, onCancel, initial }) {
  const [comment, setComment] = useState(initial?.comment || '');

  function submit(e) {
    e.preventDefault();
    if (!comment.trim()) return;

    onSave({
      line,
      ...(endLine ? { end_line: endLine } : {}),
      comment: comment.trim(),
      suggestion: '',
    });
  }

  const label = endLine ? `Lines ${line}–${endLine}` : `Line ${line}`;

  return (
    <form className="comment-form" onSubmit={submit}>
      <div className="comment-meta">{label}</div>
      <label>
        Comment
        <RichAnswerEditor
          value={comment}
          onChange={setComment}
          ariaLabel="Comment"
          placeholder="Describe the issue and why it matters"
          hintText=""
          compact={true}
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
