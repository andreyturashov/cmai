import React, { useMemo, useState } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import CommentForm from './CommentForm';

export default function CodeReviewPanel({
  code,
  language,
  comments,
  onAddComment,
  onSubmitReview,
  reviewerName,
  setReviewerName,
}) {
  const [activeLine, setActiveLine] = useState(null);
  const lines = useMemo(() => (code ? code.split('\n') : []), [code]);
  const prismLanguage = useMemo(() => {
    const requested = (language || 'python').toLowerCase();
    return Prism.languages[requested] ? requested : 'python';
  }, [language]);

  const commentsByLine = useMemo(() => {
    return comments.reduce((acc, c) => {
      acc[c.line] = acc[c.line] || [];
      acc[c.line].push(c);
      return acc;
    }, {});
  }, [comments]);

  return (
    <section className="right-panel card reveal">
      <header className="review-header">
        <h3>Code Viewer</h3>
        <div className="reviewer-wrap">
          <label>
            Reviewer
            <input
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              placeholder="Your name"
            />
          </label>
          <button onClick={onSubmitReview} disabled={!comments.length || !reviewerName.trim()}>
            Submit Review
          </button>
        </div>
      </header>

      <div className="code-scroll">
        {lines.map((line, idx) => {
          const lineNumber = idx + 1;
          return (
            <div key={lineNumber} className="code-line-block">
              <button className="code-line" onClick={() => setActiveLine(lineNumber)}>
                <span className="line-no">{lineNumber}</span>
                <code
                  dangerouslySetInnerHTML={{
                    __html:
                      Prism.highlight(line || ' ', Prism.languages[prismLanguage], prismLanguage) || '&nbsp;',
                  }}
                />
              </button>

              {commentsByLine[lineNumber]?.map((c, i) => (
                <div key={`${lineNumber}-${i}`} className="inline-comment">
                  {c.comment}
                  {c.suggestion ? <p>Fix: {c.suggestion}</p> : null}
                </div>
              ))}

              {activeLine === lineNumber ? (
                <CommentForm
                  line={lineNumber}
                  onSave={(comment) => {
                    onAddComment(comment);
                    setActiveLine(null);
                  }}
                  onCancel={() => setActiveLine(null)}
                />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
