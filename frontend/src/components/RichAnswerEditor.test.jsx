import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import RichAnswerEditor from './RichAnswerEditor';

describe('RichAnswerEditor', () => {
  it('renders the lexical textbox and formatting hint', () => {
    render(<RichAnswerEditor value="" onChange={vi.fn()} />);

    expect(screen.getByRole('textbox', { name: 'Your Answer' })).toBeInTheDocument();
    expect(
      screen.getByText(
        /Supports markdown shortcuts for bold, lists, links, and inline or fenced code blocks./i,
      ),
    ).toBeInTheDocument();
  });

  it('supports compact comment editor configuration', () => {
    render(
      <RichAnswerEditor
        value=""
        onChange={vi.fn()}
        ariaLabel="Comment"
        placeholder="Describe the issue and why it matters"
        hintText=""
        compact={true}
      />,
    );

    expect(screen.getByRole('textbox', { name: 'Comment' })).toBeInTheDocument();
    expect(screen.getByText('Describe the issue and why it matters')).toBeInTheDocument();
    expect(
      screen.queryByText(
        /Supports markdown shortcuts for bold, lists, links, and inline or fenced code blocks./i,
      ),
    ).not.toBeInTheDocument();
  });
});
