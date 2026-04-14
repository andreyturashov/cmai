import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LeftPanel from './LeftPanel';

const mockTask = {
  title: 'Validate User Input',
  description: 'A function that processes user registration',
  requirements: ['Check empty fields', 'Validate email format'],
};

describe('LeftPanel', () => {
  it('shows loading when task is null', () => {
    render(<LeftPanel task={null} aiAnalysis={null} aiLoading={false} />);
    expect(screen.getByText('Loading task...')).toBeInTheDocument();
  });

  it('renders task title and description', () => {
    render(<LeftPanel task={mockTask} aiAnalysis={null} aiLoading={false} />);
    expect(screen.getByText('Validate User Input')).toBeInTheDocument();
    expect(screen.getByText('A function that processes user registration')).toBeInTheDocument();
  });

  it('renders requirements list', () => {
    render(<LeftPanel task={mockTask} aiAnalysis={null} aiLoading={false} />);
    expect(screen.getByText('Check empty fields')).toBeInTheDocument();
    expect(screen.getByText('Validate email format')).toBeInTheDocument();
  });

  it('shows loading spinner when aiLoading', () => {
    render(<LeftPanel task={mockTask} aiAnalysis={null} aiLoading={true} />);
    expect(screen.getByText(/Analyzing with Ollama/)).toBeInTheDocument();
  });

  it('shows error state when aiAnalysis has error', () => {
    render(<LeftPanel task={mockTask} aiAnalysis={{ error: true }} aiLoading={false} />);
    expect(screen.getByText('AI analysis unavailable')).toBeInTheDocument();
  });

  it('shows AI analysis results when available', () => {
    const analysis = {
      analysis: {
        all_fixed: true,
        score: 8.5,
        detected_critical: 2,
        total_critical: 2,
        detected_medium: 1,
        total_medium: 1,
        detected_low: 0,
        total_low: 1,
        missed_issues: ['low-1'],
        feedback: ['Consider maintainability improvements.'],
        summary: 'Good review overall.',
        issues: [
          {
            issue_id: 'c-1',
            title: 'SQL Injection',
            severity: 'critical',
            addressed: true,
            explanation: 'Found it',
          },
          {
            issue_id: 'm-1',
            title: 'Error handling',
            severity: 'medium',
            addressed: true,
            explanation: 'Addressed',
          },
        ],
      },
    };

    render(<LeftPanel task={mockTask} aiAnalysis={analysis} aiLoading={false} />);
    expect(screen.getByText('✓ All issues addressed')).toBeInTheDocument();
    expect(screen.getByText('Score: 8.5 / 10')).toBeInTheDocument();
    expect(screen.getByText('Good review overall.')).toBeInTheDocument();
    expect(screen.getByText('Consider maintainability improvements.')).toBeInTheDocument();
    expect(screen.getByText(/Missed: low-1/)).toBeInTheDocument();
  });

  it('shows fail badge when not all fixed', () => {
    const analysis = {
      analysis: {
        all_fixed: false,
        score: 3.0,
        detected_critical: 0,
        total_critical: 1,
        detected_medium: 0,
        total_medium: 1,
        detected_low: 0,
        total_low: 0,
        missed_issues: [],
        feedback: ['Focus on high-impact failures.'],
        summary: '',
        issues: [],
      },
    };

    render(<LeftPanel task={mockTask} aiAnalysis={analysis} aiLoading={false} />);
    expect(screen.getByText('✗ Some issues remain')).toBeInTheDocument();
  });

  it('renders issue verdicts with addressed/missed icons', () => {
    const analysis = {
      analysis: {
        all_fixed: false,
        score: 5,
        detected_critical: 1,
        total_critical: 1,
        detected_medium: 0,
        total_medium: 1,
        detected_low: 0,
        total_low: 0,
        missed_issues: [],
        feedback: ['Good effort.'],
        summary: '',
        issues: [
          {
            issue_id: 'c-1',
            title: 'Buffer overflow',
            severity: 'critical',
            addressed: true,
            explanation: 'Caught',
          },
          {
            issue_id: 'm-1',
            title: 'Logging',
            severity: 'medium',
            addressed: false,
            explanation: 'Missed',
          },
        ],
      },
    };

    render(<LeftPanel task={mockTask} aiAnalysis={analysis} aiLoading={false} />);
    expect(screen.getByText('Buffer overflow')).toBeInTheDocument();
    expect(screen.getByText('Logging')).toBeInTheDocument();
    expect(screen.getByText('Caught')).toBeInTheDocument();
    expect(screen.getByText('Missed')).toBeInTheDocument();
  });

  it('does not render AI section when no analysis and not loading', () => {
    const { container } = render(<LeftPanel task={mockTask} aiAnalysis={null} aiLoading={false} />);
    expect(container.querySelector('.ai-section')).toBeNull();
    expect(container.querySelector('.eval-section')).toBeNull();
  });
});
