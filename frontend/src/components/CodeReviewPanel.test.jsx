import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import CodeReviewPanel from './CodeReviewPanel';

const sampleCode = 'def foo():\n    return 42\n    print("unreachable")';

const defaults = {
  code: sampleCode,
  language: 'python',
  instructions: [],
  responseMode: 'comments',
  comments: [],
  answer: '',
  referenceIssues: [],
  showReference: false,
  onToggleReference: vi.fn(),
  onAddComment: vi.fn(),
  onEditComment: vi.fn(),
  onAnswerChange: vi.fn(),
  onSubmitReview: vi.fn(),
};

describe('CodeReviewPanel', () => {
  it('renders code lines', () => {
    render(<CodeReviewPanel {...defaults} />);
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders Show Answer button', () => {
    render(<CodeReviewPanel {...defaults} />);
    expect(screen.getByText('Show Answer')).toBeInTheDocument();
  });

  it('renders Hide Answer when showReference is true', () => {
    render(<CodeReviewPanel {...defaults} showReference={true} />);
    expect(screen.getByText('Hide Answer')).toBeInTheDocument();
  });

  it('calls onToggleReference when toggle clicked', async () => {
    const onToggle = vi.fn();
    render(<CodeReviewPanel {...defaults} onToggleReference={onToggle} />);
    await userEvent.click(screen.getByText('Show Answer'));
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it('calls onSubmitReview when Submit Review clicked', async () => {
    const onSubmit = vi.fn();
    render(<CodeReviewPanel {...defaults} onSubmitReview={onSubmit} />);
    await userEvent.click(screen.getByText('Submit Review'));
    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it('renders answer textarea in answer mode', () => {
    render(<CodeReviewPanel {...defaults} responseMode="answer" />);
    expect(screen.getByText('Your Answer')).toBeInTheDocument();
  });

  it('disables submit in answer mode until there is an answer', () => {
    render(<CodeReviewPanel {...defaults} responseMode="answer" answer="" />);
    expect(screen.getByText('Submit Review')).toBeDisabled();
  });

  it('updates answer text in answer mode', async () => {
    const onAnswerChange = vi.fn();
    render(<CodeReviewPanel {...defaults} responseMode="answer" onAnswerChange={onAnswerChange} />);
    await userEvent.type(
      screen.getByPlaceholderText('Write your answer here'),
      'Tuple is immutable',
    );
    expect(onAnswerChange).toHaveBeenCalled();
  });

  it('renders inline comments', () => {
    const comments = [{ line: 2, comment: 'Unreachable code below', suggestion: 'Remove it' }];
    render(<CodeReviewPanel {...defaults} comments={comments} />);
    expect(screen.getByText('Unreachable code below')).toBeInTheDocument();
    expect(screen.getByText('Line 2')).toBeInTheDocument();
  });

  it('renders range comment label', () => {
    const comments = [
      { line: 1, end_line: 3, comment: 'Whole function issue', suggestion: 'Rewrite' },
    ];
    render(<CodeReviewPanel {...defaults} comments={comments} />);
    expect(screen.getByText('Lines 1–3')).toBeInTheDocument();
  });

  it('renders suggestion in comment', () => {
    const comments = [{ line: 1, comment: 'Bad pattern', suggestion: 'Use a guard clause' }];
    render(<CodeReviewPanel {...defaults} comments={comments} />);
    expect(screen.getByText('Use a guard clause')).toBeInTheDocument();
  });

  it('renders reference issues when shown', () => {
    const refs = [
      {
        id: 'ref-1',
        line: 2,
        title: 'Dead code',
        severity: 'low',
        description: 'Remove unreachable',
      },
    ];
    const { container } = render(
      <CodeReviewPanel {...defaults} referenceIssues={refs} showReference={true} />,
    );
    expect(container.querySelector('.code-line-ref')).not.toBeNull();
  });

  it('shows comment form on line selection', () => {
    render(<CodeReviewPanel {...defaults} />);
    const lineNo = screen.getByText('2');
    fireEvent.mouseDown(lineNo);
    fireEvent.mouseUp(lineNo.closest('.code-scroll') || document);
    expect(screen.getByText('Save Comment')).toBeInTheDocument();
  });

  it('does not open comment form in answer mode', () => {
    render(<CodeReviewPanel {...defaults} responseMode="answer" />);
    const lineNo = screen.getByText('2');
    fireEvent.mouseDown(lineNo);
    fireEvent.mouseUp(lineNo.closest('.code-scroll') || document);
    expect(screen.queryByText('Save Comment')).not.toBeInTheDocument();
  });

  it('handles empty code gracefully', () => {
    render(<CodeReviewPanel {...defaults} code="" />);
    expect(screen.getByText('Code Viewer')).toBeInTheDocument();
  });

  it('falls back to python for unknown language', () => {
    render(<CodeReviewPanel {...defaults} language="brainfuck" />);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('shows edit form when Edit clicked', async () => {
    const comments = [{ line: 1, comment: 'Issue here', suggestion: 'Fix this' }];
    render(<CodeReviewPanel {...defaults} comments={comments} />);
    await userEvent.click(screen.getByText('Edit'));
    // Should show a CommentForm prefilled
    const textareas = screen.getAllByRole('textbox');
    expect(textareas[0]).toHaveValue('Issue here');
    expect(textareas[1]).toHaveValue('Fix this');
  });

  it('supports multi-line selection via drag', () => {
    render(<CodeReviewPanel {...defaults} />);
    const line1 = screen.getByText('1');
    const line3 = screen.getByText('3');
    const scrollContainer = line1.closest('.code-scroll');

    fireEvent.mouseDown(line1);
    fireEvent.mouseEnter(line3);
    fireEvent.mouseUp(scrollContainer || document);

    expect(screen.getByText('Lines 1–3')).toBeInTheDocument();
  });

  it('ignores mouseEnter when not dragging', () => {
    render(<CodeReviewPanel {...defaults} />);
    const line2 = screen.getByText('2');
    // mouseEnter without preceding mouseDown should not create selection
    fireEvent.mouseEnter(line2.closest('.code-line'));
    expect(screen.queryByText('Save Comment')).not.toBeInTheDocument();
  });

  it('clears selection on mouseLeave', () => {
    render(<CodeReviewPanel {...defaults} />);
    const line1 = screen.getByText('1');
    const scrollContainer = line1.closest('.code-scroll');

    fireEvent.mouseDown(line1);
    fireEvent.mouseLeave(scrollContainer);
    // dragging ended — form should appear for single line
    expect(screen.getByText('Save Comment')).toBeInTheDocument();
  });

  it('adds comment via the inline form', async () => {
    const onAdd = vi.fn();
    render(<CodeReviewPanel {...defaults} onAddComment={onAdd} />);

    // Select line 1
    const line1 = screen.getByText('1');
    fireEvent.mouseDown(line1);
    fireEvent.mouseUp(line1.closest('.code-scroll') || document);

    const [commentArea, suggestionArea] = screen.getAllByRole('textbox');
    await userEvent.type(commentArea, 'Bug found');
    await userEvent.type(suggestionArea, 'Fix it');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(onAdd).toHaveBeenCalledWith({
      line: 1,
      comment: 'Bug found',
      suggestion: 'Fix it',
    });
  });

  it('cancels selection via the inline form cancel', async () => {
    render(<CodeReviewPanel {...defaults} />);
    const line1 = screen.getByText('1');
    fireEvent.mouseDown(line1);
    fireEvent.mouseUp(line1.closest('.code-scroll') || document);

    expect(screen.getByText('Save Comment')).toBeInTheDocument();
    await userEvent.click(screen.getByText('Cancel'));
    expect(screen.queryByText('Save Comment')).not.toBeInTheDocument();
  });

  it('saves edited comment via edit form', async () => {
    const onEdit = vi.fn();
    const comments = [{ line: 1, comment: 'Old comment', suggestion: 'Old fix' }];
    render(<CodeReviewPanel {...defaults} comments={comments} onEditComment={onEdit} />);

    await userEvent.click(screen.getByText('Edit'));
    const textareas = screen.getAllByRole('textbox');
    await userEvent.clear(textareas[0]);
    await userEvent.type(textareas[0], 'New comment');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(onEdit).toHaveBeenCalledWith(0, expect.objectContaining({ comment: 'New comment' }));
  });

  it('cancels edit form', async () => {
    const comments = [{ line: 1, comment: 'Comment', suggestion: 'Fix' }];
    render(<CodeReviewPanel {...defaults} comments={comments} />);

    await userEvent.click(screen.getByText('Edit'));
    await userEvent.click(screen.getByText('Cancel'));
    // Original comment should still be visible
    expect(screen.getByText('Comment')).toBeInTheDocument();
  });

  it('renders reference issue with code block', () => {
    const refs = [
      {
        id: 'ref-1',
        line: 1,
        title: 'Security issue',
        severity: 'critical',
        description: 'SQL injection risk',
        suggestion: 'Use parameterized queries',
        code: 'cursor.execute(sql, params)',
      },
    ];
    render(<CodeReviewPanel {...defaults} referenceIssues={refs} showReference={true} />);
    expect(screen.getByText('Security issue')).toBeInTheDocument();
    expect(screen.getByText('SQL injection risk')).toBeInTheDocument();
    expect(screen.getByText('Corrected code')).toBeInTheDocument();
    expect(screen.getByText('cursor.execute(sql, params)')).toBeInTheDocument();
  });

  it('renders reference issue without code block', () => {
    const refs = [
      {
        id: 'ref-2',
        line: 2,
        title: 'Style issue',
        severity: 'low',
        description: 'Inconsistent naming',
        suggestion: 'Use camelCase',
      },
    ];
    render(<CodeReviewPanel {...defaults} referenceIssues={refs} showReference={true} />);
    expect(screen.getByText('Style issue')).toBeInTheDocument();
    expect(screen.queryByText('Corrected code')).not.toBeInTheDocument();
  });
});
