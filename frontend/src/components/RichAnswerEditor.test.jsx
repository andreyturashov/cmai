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
});
