import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ArenaPage from './pages/arena/ArenaPage';
import { ArenaPriorities } from './pages/arena/ArenaPriorities';
import '@testing-library/jest-dom/vitest';

// Mock apiV2 methods
vi.mock('./lib/api-client-v2', () => ({
  apiV2: {
    getCompare: vi.fn().mockImplementation((topic: string) => {
      if (topic === 'leaderboard') {
        return Promise.resolve({
          variant: 'nonlinear',
          champion_key: 'rf',
          champion_rule: 'ADR-009 Balanced MCDA',
          metrics: [
            { key: 'rf', name: 'Random Forest', family: 'ensemble', macro_f1: 0.780, macro_f1_ci_low: 0.762, macro_f1_ci_high: 0.798, accuracy: 0.777, qwk: 0.784, ece: 0.0133, inference_latency_p95_ms: 99.4, is_champion: true },
            { key: 'boost', name: 'Histogram Gradient Boosting', family: 'boosting', macro_f1: 0.804, macro_f1_ci_low: 0.785, macro_f1_ci_high: 0.821, accuracy: 0.801, qwk: 0.807, ece: 0.0904, inference_latency_p95_ms: 105.8 },
          ],
        });
      }
      return Promise.resolve({});
    }),
    postLLMVerdict: vi.fn().mockResolvedValue({
      headline: 'Random Forest Recommended Under Balanced Weights',
      recommendation: { model_key: 'rf', confidence: 'high', decision_strength: 'marginal' },
      claims: [{ statement: 'Random forest delivers minimal calibration error.', fact_ids: ['F12'] }],
      trade_offs: ['Ensemble tree memory vs speed'],
      caveats: ['Rankings depend on synthetic generator'],
      why_not: { boost: 'Higher ECE calibration error' },
      validation: { passed: true, errors: [], source: 'llm', checks_evaluated: 16 },
      evidence_packet_hash: 'abc123hash',
    }),
    postMCDA: vi.fn().mockImplementation((weights: Record<string, number>, profile: string) => {
      return Promise.resolve({
        weights_used: weights,
        profile_name: profile,
        winner: 'rf',
        decision_strength: 'marginal',
        decision_rule: 'ADR-009 Rule',
        ranked_models: [
          { key: 'rf', composite_score: 0.573, rank: 1, rank1_probability: 0.642, decision_strength: 'marginal' },
          { key: 'boost', composite_score: 0.540, rank: 2, rank1_probability: 0.280, decision_strength: 'marginal' },
        ],
      });
    }),
  },
}));

describe('ArenaPage Container', () => {
  it('renders all 9 navigation tabs', () => {
    render(<ArenaPage />);
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Priorities (MCDA)')).toBeInTheDocument();
    expect(screen.getByText('Head-to-Head')).toBeInTheDocument();
    expect(screen.getByText('Metrics Deep Dive')).toBeInTheDocument();
    expect(screen.getByText('Cost & Speed')).toBeInTheDocument();
    expect(screen.getByText('Data Sensitivity')).toBeInTheDocument();
    expect(screen.getByText('Explainability')).toBeInTheDocument();
    expect(screen.getByText('Fairness & Robustness')).toBeInTheDocument();
    expect(screen.getByText('LLM Verdict')).toBeInTheDocument();
  });

  it('switches to Priorities tab on click', async () => {
    render(<ArenaPage />);
    const prioTab = screen.getByText('Priorities (MCDA)');
    fireEvent.click(prioTab);
    await waitFor(() => {
      expect(screen.getByText(/Multi-Criteria Decision Analysis/i)).toBeInTheDocument();
    });
  });
});

describe('ArenaPriorities Component', () => {
  it('renders presets and triggers MCDA evaluation', async () => {
    render(<ArenaPriorities />);
    await waitFor(() => {
      expect(screen.getByText('Priority Profiles')).toBeInTheDocument();
      expect(screen.getByText(/Decision Strength/i)).toBeInTheDocument();
    });
  });
});
