import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import EvaluationCard from './EvaluationCard';

describe('EvaluationCard', () => {
  it('renders nothing when data is null', () => {
    const { container } = render(<EvaluationCard data={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders evaluation score and stats', () => {
    const data = {
      evaluation: {
        score: 7.5,
        detected_critical: 2,
        total_critical: 3,
        detected_medium: 1,
        total_medium: 2,
        detected_low: 0,
        total_low: 1,
        missed_issue_ids: ['low-1'],
        feedback: ['Focus on critical issues first.'],
      },
    };

    render(<EvaluationCard data={data} />);
    expect(screen.getByText('AI Evaluation')).toBeInTheDocument();
    expect(screen.getByText('Score: 7.5 / 10')).toBeInTheDocument();
    expect(screen.getByText(/Missed issues: low-1/)).toBeInTheDocument();
    expect(screen.getByText('Focus on critical issues first.')).toBeInTheDocument();
  });

  it('shows None when no missed issues', () => {
    const data = {
      evaluation: {
        score: 10,
        detected_critical: 1,
        total_critical: 1,
        detected_medium: 1,
        total_medium: 1,
        detected_low: 1,
        total_low: 1,
        missed_issue_ids: [],
        feedback: ['Perfect!'],
      },
    };

    render(<EvaluationCard data={data} />);
    expect(screen.getByText(/Missed issues: None/)).toBeInTheDocument();
  });
});
