import React, { useCallback, useMemo, useRef, useState } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-graphql';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-sql';
import CommentForm from './CommentForm';
import MarkdownContent from './MarkdownContent';
import RichAnswerEditor from './RichAnswerEditor';

const LANGUAGE_ALIASES = {
  django: 'python',
  fastapi: 'python',
  react: 'javascript',
};

export default function CodeReviewPanel({
  code,
  language,
  instructions = [],
  responseMode = 'comments',
  comments = [],
  answer = '',
  answerEditorKey = 'answer-editor',
  referenceIssues = [],
  showReference,
  onToggleReference,
  onAddComment,
  onEditComment,
  onAnswerChange,
  onSubmitReview,
  readOnly = false,
  savedAnswer = '',
  title = 'Code',
  referenceIssueCount = 0,
  showHeader = true,
  eyebrowLabel = '',
  isCompleted = false,
}) {
  const [selStart, setSelStart] = useState(null);
  const [selEnd, setSelEnd] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [editingIdx, setEditingIdx] = useState(null);
  const dragStart = useRef(null);
  const lines = useMemo(() => (code ? code.split('\n') : []), [code]);
  const prismLanguage = useMemo(() => {
    const requested =
      LANGUAGE_ALIASES[(language || 'python').toLowerCase()] ||
      (language || 'python').toLowerCase();
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

  const inlineReferenceIssues = useMemo(
    () => (responseMode === 'answer' ? [] : referenceIssues),
    [referenceIssues, responseMode],
  );

  const theoryReferenceIssues = useMemo(
    () => (responseMode === 'answer' ? referenceIssues : []),
    [referenceIssues, responseMode],
  );

  const refByLine = useMemo(() => {
    return inlineReferenceIssues.reduce((acc, issue) => {
      acc[issue.line] = acc[issue.line] || [];
      acc[issue.line].push(issue);
      return acc;
    }, {});
  }, [inlineReferenceIssues]);

  const selMin = selStart != null && selEnd != null ? Math.min(selStart, selEnd) : selStart;
  const selMax = selStart != null && selEnd != null ? Math.max(selStart, selEnd) : selStart;

  const editingComment = editingIdx != null ? comments[editingIdx] : null;
  const editMin = editingComment?.line ?? null;
  const editMax = editingComment?.end_line ?? editMin;

  function handleMouseDown(lineNumber, e) {
    if (responseMode !== 'comments' || readOnly) return;
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
  }, []);

  const showForm = responseMode === 'comments' && !readOnly && selStart != null && !dragging;
  const panelInstructions = instructions.length
    ? instructions
    : [
        'Review the code',
        'Add inline comments',
        'Explain impact and risk',
        'Suggest improvements',
        '(Optional) Provide fixed code',
      ];
  const submitDisabled = responseMode === 'answer' ? !answer.trim() : false;
  const hasReferenceIssues = referenceIssueCount > 0;

  return (
    <section className="right-panel card reveal">
      {showHeader ? (
        <header className="review-header">
          <div className="review-title">
            <p className="eyebrow">{title}</p>
            <div className="info-icon-wrap">
              <span className="info-icon">&#9432;</span>
              <div className="info-tooltip">
                <strong>Instructions</strong>
                <ol>
                  {panelInstructions.map((instruction) => (
                    <li key={instruction}>{instruction}</li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
          <div className="review-header-actions">
            {hasReferenceIssues && !isCompleted ? (
              <button
                className={`ghost toggle-ref${showReference ? ' toggle-ref-active' : ''}`}
                onClick={onToggleReference}
              >
                {showReference ? 'Hide Answer' : 'Show Answer'}
              </button>
            ) : null}
            {!readOnly && !isCompleted ? (
              <button onClick={onSubmitReview} disabled={submitDisabled}>
                Submit Review
              </button>
            ) : null}
          </div>
        </header>
      ) : null}

      {!showHeader && eyebrowLabel ? <p className="eyebrow">{eyebrowLabel}</p> : null}

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
          ]
            .filter(Boolean)
            .join(' ');
          return (
            <div key={lineNumber} className="code-line-block">
              <div className={lineClasses} onMouseEnter={() => handleMouseEnter(lineNumber)}>
                <span className="line-no" onMouseDown={(e) => handleMouseDown(lineNumber, e)}>
                  {lineNumber}
                </span>
                <code
                  dangerouslySetInnerHTML={{
                    __html:
                      Prism.highlight(line || ' ', Prism.languages[prismLanguage], prismLanguage) ||
                      '&nbsp;',
                  }}
                />
              </div>

              {commentsByLine[lineNumber]?.map((c, i) => {
                const globalIdx = comments.indexOf(c);
                if (editingIdx === globalIdx) return null;
                const rangeLabel = c.end_line ? `Lines ${c.line}–${c.end_line}` : `Line ${c.line}`;
                return (
                  <div key={`${lineNumber}-${i}`} className="inline-comment">
                    <div className="inline-comment-header">
                      <MarkdownContent
                        content={c.comment}
                        className="comment-text markdown-content"
                      />
                      <div className="inline-comment-actions">
                        <span className="comment-meta">{rangeLabel}</span>
                        {!readOnly ? (
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
                        ) : null}
                      </div>
                    </div>
                    {c.suggestion ? (
                      <p className="comment-suggestion-text">Suggestion: {c.suggestion}</p>
                    ) : null}
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
                  <p className="ref-suggestion-text">{issue.suggestion}</p>
                  {issue.code ? (
                    <div className="ref-code-block">
                      <span className="ref-code-label">Corrected code</span>
                      <pre className="ref-code">
                        <code>{issue.code}</code>
                      </pre>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          );
        })}
      </div>

      {responseMode === 'answer' && showReference && theoryReferenceIssues.length ? (
        <section className="theory-answer-panel">
          <p className="eyebrow">Expected Answer</p>
          {theoryReferenceIssues.map((issue) => (
            <div key={issue.id} className="ref-issue ref-issue-static">
              <div className="ref-issue-header">
                <span className={`ref-severity sev-${issue.severity}`}>{issue.severity}</span>
                <strong className="ref-title">{issue.title}</strong>
              </div>
              <p className="ref-description ref-description-wrap">{issue.description}</p>
              <p className="ref-suggestion-text">{issue.suggestion}</p>
              {issue.code ? (
                <div className="ref-code-block">
                  <span className="ref-code-label">Expected answer</span>
                  <pre className="ref-code ref-code-wrap">
                    <code>{issue.code}</code>
                  </pre>
                </div>
              ) : null}
            </div>
          ))}
        </section>
      ) : null}

      {responseMode === 'answer' ? (
        <div className="answer-form">
          <label>
            Your Answer
            {readOnly ? (
              <div className="saved-answer-card">
                {savedAnswer.trim() ? (
                  <MarkdownContent content={savedAnswer} className="markdown-content" />
                ) : (
                  <p className="muted">No written answer was saved for this submission.</p>
                )}
              </div>
            ) : (
              <RichAnswerEditor
                key={answerEditorKey}
                value={answer}
                onChange={onAnswerChange}
                ariaLabel="Your Answer"
              />
            )}
          </label>
        </div>
      ) : null}
    </section>
  );
}
