import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import CommentForm from './CommentForm';

vi.mock('./RichAnswerEditor', () => ({
  default: function MockRichAnswerEditor({ value = '', onChange, ariaLabel = 'Comment' }) {
    return (
      <textarea
        aria-label={ariaLabel}
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
      />
    );
  },
}));

describe('CommentForm', () => {
  const defaults = {
    line: 5,
    endLine: null,
    onSave: vi.fn(),
    onCancel: vi.fn(),
  };

  it('renders with line label', () => {
    render(<CommentForm {...defaults} />);
    expect(screen.getByText('Line 5')).toBeInTheDocument();
  });

  it('renders with range label', () => {
    render(<CommentForm {...defaults} endLine={10} />);
    expect(screen.getByText('Lines 5–10')).toBeInTheDocument();
  });

  it('calls onCancel when cancel clicked', async () => {
    const onCancel = vi.fn();
    render(<CommentForm {...defaults} onCancel={onCancel} />);
    await userEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('calls onSave with comment data on submit', async () => {
    const onSave = vi.fn();
    render(<CommentForm {...defaults} onSave={onSave} />);

    await userEvent.type(screen.getByRole('textbox', { name: 'Comment' }), 'Missing validation');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(onSave).toHaveBeenCalledWith({
      line: 5,
      comment: 'Missing validation',
      suggestion: '',
    });
  });

  it('includes end_line when range is selected', async () => {
    const onSave = vi.fn();
    render(<CommentForm {...defaults} endLine={8} onSave={onSave} />);

    await userEvent.type(screen.getByRole('textbox', { name: 'Comment' }), 'Bug');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(onSave).toHaveBeenCalledWith({
      line: 5,
      end_line: 8,
      comment: 'Bug',
      suggestion: '',
    });
  });

  it('does not submit when comment is empty', async () => {
    const onSave = vi.fn();
    render(<CommentForm {...defaults} onSave={onSave} />);

    await userEvent.click(screen.getByText('Save Comment'));

    expect(onSave).not.toHaveBeenCalled();
  });

  it('prefills from initial values', () => {
    const initial = { comment: 'existing', suggestion: 'fix code' };
    render(<CommentForm {...defaults} initial={initial} />);

    expect(screen.getByRole('textbox', { name: 'Comment' })).toHaveValue('existing');
    expect(screen.queryByDisplayValue('fix code')).not.toBeInTheDocument();
  });
});
