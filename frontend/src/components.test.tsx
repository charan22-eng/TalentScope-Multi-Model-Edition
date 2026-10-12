import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ClassChip } from './components/ui/ClassChip';
import '@testing-library/jest-dom/vitest';

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('ClassChip', () => {
  it('renders High chip with correct text and class', () => {
    render(<ClassChip status="High" />);
    const el = screen.getByRole('status');
    expect(el).toHaveClass('chip-high');
    expect(el).toHaveTextContent('High');
  });

  it('renders Unknown fallback', () => {
    const invalidStatus = 'FooBar' as unknown as 'Low';
    render(<ClassChip status={invalidStatus} />);
    const el = screen.getByRole('status');
    expect(el).toHaveClass('chip-unknown');
    expect(el).toHaveTextContent('Unknown');
  });
});

import { ModelChip } from './components/ui/ModelChip';
import { CIWhisker } from './components/charts/CIWhisker';
import { DivergingBar } from './components/charts/DivergingBar';
import { BumpChart } from './components/charts/BumpChart';

describe('ModelChip', () => {
  it('renders Random Forest with Champion badge and star marker', () => {
    render(<ModelChip modelKey="rf" showChampionBadge={true} />);
    const chip = screen.getByRole('status');
    expect(chip).toHaveTextContent('Random Forest');
    expect(chip).toHaveTextContent(/Champion/i);
    expect(chip).toHaveTextContent('★');
  });

  it('renders KNN with diamond marker', () => {
    render(<ModelChip modelKey="knn" />);
    const chip = screen.getByRole('status');
    expect(chip).toHaveTextContent('K-Nearest Neighbours');
    expect(chip).toHaveTextContent('◆');
  });

  it('renders with button role when onClick is provided', () => {
    const handleClick = vi.fn();
    render(<ModelChip modelKey="boost" onClick={handleClick} active={true} />);
    const btn = screen.getByRole('button');
    expect(btn).toHaveAttribute('aria-pressed', 'true');
    btn.click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe('CIWhisker', () => {
  it('renders point estimate and 95% CI bounds', () => {
    render(
      <CIWhisker
        modelKey="rf"
        point={0.7804}
        ciLow={0.762}
        ciHigh={0.798}
        metricName="Macro-F1"
      />
    );
    const group = screen.getByRole('group');
    expect(group).toHaveAttribute('aria-label');
    expect(screen.getByText('0.780')).toBeInTheDocument();
    expect(screen.getByText(/\[0\.762, 0\.798\]/)).toBeInTheDocument();
  });
});

describe('DivergingBar', () => {
  it('renders positive and negative deltas correctly', () => {
    render(
      <DivergingBar
        label="F1 Delta"
        value={0.0125}
        leftLabel="Model A"
        rightLabel="Model B"
      />
    );
    expect(screen.getByText('F1 Delta')).toBeInTheDocument();
    expect(screen.getByText('+0.0125')).toBeInTheDocument();
  });
});

describe('BumpChart', () => {
  it('renders SVG with column variants and lines', () => {
    const rankings = [
      { modelKey: 'rf', linearRank: 3, nonlinearRank: 1, noisyRank: 2 },
      { modelKey: 'svm', linearRank: 1, nonlinearRank: 2, noisyRank: 3 },
    ];
    render(<BumpChart rankings={rankings} />);
    expect(screen.getByLabelText('Variant sensitivity bump chart')).toBeInTheDocument();
    expect(screen.getByText('Linear')).toBeInTheDocument();
    expect(screen.getByText('Nonlinear (Default)')).toBeInTheDocument();
    expect(screen.getByText('Noisy Overlap')).toBeInTheDocument();
  });
});

