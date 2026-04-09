import React, { useCallback, useMemo, useRef, useState } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import CommentForm from './CommentForm';

export default function CodeReviewPanel({
  code,
  language,
  comments,
  referenceIssues = [],
  showReference,
  onToggleReference,
  onAddComment,
  onEditComment,
  onSubmitReview,
}) {
  const [selStart, setSelStart] = useState(null);
  const [selEnd, setSelEnd] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [editingIdx, setEditingIdx] = useState(null);
  const dragStart = useRef(null);
  const lines = useMemo(() => (code ? code.split('\n') : []), [code]);
  const prismLanguage = useMemo(() => {
    const requested = (language || 'python').toLowerCase();
    return Prism.languages[requested] ? requested : 'python';
  }, [language]);

  const commentsByLine = useMemo(() => {
    return comments.reduce((acc, c) => {
      const anchor = c.end_line || c.line;
      acc[anchor] = acc[anchor] || [];
      acc[anchor].push(c);
      return acc;
    }, {});
  }, [comments]);

  const refByLine = useMemo(() => {
    return referenceIssues.reduce((acc, issue) => {
      acc[issue.line] = acc[issue.line] || [];
      acc[issue.line].push(issue);
      return acc;
    }, {});
  }, [referenceIssues]);

  const selMin = selStart != null && selEnd != null ? Math.min(selStart, selEnd) : selStart;
  const selMax = selStart != null && selEnd != null ? Math.max(selStart, selEnd) : selStart;

  const editingComment = editingIdx != null ? comments[editingIdx] : null;
  const editMin = editingComment?.line ?? null;
  const editMax = editingComment?.end_line ?? editMin;

  function handleMouseDown(lineNumber, e) {
    e.preventDefault();
    if (editingIdx != null) setEditingIdx(null);
    dragStart.current = lineNumber;
    setDragging(true);
    setSelStart(lineNumber);
    setSelEnd(null);
  }

  function handleMouseEnter(lineNumber) {
    if (!dragging) return;
    setSelEnd(lineNumber);
  }

  function handleMouseUp() {
    if (!dragging) return;
    setDragging(false);
  }

  function clearSelection() {
    setSelStart(null);
    setSelEnd(null);
    setEditingIdx(null);
  }

  const formRef = useCallback((node) => {
    if (node) node.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [selStart, selEnd, editingIdx]);

  const showForm = selStart != null && !dragging;

  return (
    <section className="right-panel card reveal">
      <header className="review-header">
        <div className="review-title">
          <h3>Code Viewer</h3>
          <div className="info-icon-wrap">
            <span className="info-icon">&#9432;</span>
            <div className="info-tooltip">
              <strong>Instructions</strong>
              <ol>
                <li>Review the code</li>
                <li>Add inline comments</li>
                <li>Explain impact and risk</li>
                <li>Suggest improvements</li>
                <li>(Optional) Provide fixed code</li>
              </ol>
            </div>
          </div>
        </div>
        <div className="review-header-actions">
          <button className={`ghost toggle-ref${showReference ? ' toggle-ref-active' : ''}`} onClick={onToggleReference}>
            {showReference ? 'Hide Answer' : 'Show Answer'}
          </button>
          <button onClick={onSubmitReview}>
            Submit Review
          </button>
        </div>
      </header>

      <div className="code-scroll" onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}>
        {lines.map((line, idx) => {
          const lineNumber = idx + 1;
          const inSelection = selMin != null && lineNumber >= selMin && lineNumber <= selMax;
          const inEdit = editMin != null && lineNumber >= editMin && lineNumber <= editMax;
          const hasRef = !!refByLine[lineNumber];
          const lineClasses = [
            'code-line',
            (inSelection || inEdit) && 'code-line-selected',
            hasRef && 'code-line-ref',
          ].filter(Boolean).join(' ');
          return (
            <div key={lineNumber} className="code-line-block">
              <button
                className={lineClasses}
                onMouseDown={(e) => handleMouseDown(lineNumber, e)}
                onMouseEnter={() => handleMouseEnter(lineNumber)}
              >
                <span className="line-no">{lineNumber}</span>
                <code
                  dangerouslySetInnerHTML={{
                    __html:
                      Prism.highlight(line || ' ', Prism.languages[prismLanguage], prismLanguage) || '&nbsp;',
                  }}
                />
              </button>

              {commentsByLine[lineNumber]?.map((c, i) => {
                const globalIdx = comments.indexOf(c);
                if (editingIdx === globalIdx) return null;
                const rangeLabel = c.end_line ? `Lines ${c.line}–${c.end_line}` : `Line ${c.line}`;
                return (
                  <div key={`${lineNumber}-${i}`} className="inline-comment">
                    <div className="inline-comment-header">
                      <span className="comment-text">{c.comment}</span>
                      <div className="inline-comment-actions">
                        <span className="comment-meta">{rangeLabel}</span>
                        <button
                          type="button"
                          className="ghost edit-btn"
                          onClick={() => {
                            setEditingIdx(globalIdx);
                            setSelStart(null);
                            setSelEnd(null);
                          }}
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                    {c.suggestion ? <pre className="comment-suggestion"><code>{c.suggestion}</code></pre> : null}
                  </div>
                );
              })}

              {showForm && selMax === lineNumber ? (
                <div ref={formRef}>
                  <CommentForm
                    line={selMin}
                    endLine={selMax !== selMin ? selMax : null}
                    onSave={(comment) => {
                      onAddComment(comment);
                      clearSelection();
                    }}
                    onCancel={clearSelection}
                  />
                </div>
              ) : null}

              {editingIdx != null && editMax === lineNumber ? (
                <div ref={formRef}>
                  <CommentForm
                    line={editMin}
                    endLine={editMax !== editMin ? editMax : null}
                    initial={editingComment}
                    onSave={(updated) => {
                      onEditComment(editingIdx, updated);
                      setEditingIdx(null);
                    }}
                    onCancel={() => setEditingIdx(null)}
                  />
                </div>
              ) : null}

              {refByLine[lineNumber]?.map((issue) => (
                <div key={issue.id} className="ref-issue">
                  <div className="ref-issue-header">
                    <span className={`ref-severity sev-${issue.severity}`}>{issue.severity}</span>
                    <strong className="ref-title">{issue.title}</strong>
                  </div>
                  <p className="ref-description">{issue.description}</p>
                  {issue.suggestion ? (
                    <pre className="ref-suggestion"><code>{issue.suggestion}</code></pre>
                  ) : null}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </section>
  );
}
