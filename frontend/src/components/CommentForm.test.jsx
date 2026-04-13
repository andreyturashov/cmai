import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import CommentForm from './CommentForm';

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

    const [commentArea, suggestionArea] = screen.getAllByRole('textbox');
    await userEvent.type(commentArea, 'Missing validation');
    await userEvent.type(suggestionArea, 'Add input check');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(onSave).toHaveBeenCalledWith({
      line: 5,
      comment: 'Missing validation',
      suggestion: 'Add input check',
    });
  });

  it('includes end_line when range is selected', async () => {
    const onSave = vi.fn();
    render(<CommentForm {...defaults} endLine={8} onSave={onSave} />);

    const [commentArea, suggestionArea] = screen.getAllByRole('textbox');
    await userEvent.type(commentArea, 'Bug');
    await userEvent.type(suggestionArea, 'Fix it');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(onSave).toHaveBeenCalledWith({
      line: 5,
      end_line: 8,
      comment: 'Bug',
      suggestion: 'Fix it',
    });
  });

  it('does not submit when comment is empty', async () => {
    const onSave = vi.fn();
    render(<CommentForm {...defaults} onSave={onSave} />);

    const [, suggestionArea] = screen.getAllByRole('textbox');
    await userEvent.type(suggestionArea, 'Fix');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(onSave).not.toHaveBeenCalled();
  });

  it('does not submit when suggestion is empty', async () => {
    const onSave = vi.fn();
    render(<CommentForm {...defaults} onSave={onSave} />);

    const [commentArea] = screen.getAllByRole('textbox');
    await userEvent.type(commentArea, 'Issue');
    await userEvent.click(screen.getByText('Save Comment'));

    expect(onSave).not.toHaveBeenCalled();
  });

  it('prefills from initial values', () => {
    const initial = { comment: 'existing', suggestion: 'fix code' };
    render(<CommentForm {...defaults} initial={initial} />);

    const [commentArea, suggestionArea] = screen.getAllByRole('textbox');
    expect(commentArea).toHaveValue('existing');
    expect(suggestionArea).toHaveValue('fix code');
  });
});
