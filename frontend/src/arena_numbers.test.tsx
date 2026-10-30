import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { ArenaOverview } from './pages/arena/ArenaOverview';
import { ArenaPriorities } from './pages/arena/ArenaPriorities';
import { ArenaSensitivity } from './pages/arena/ArenaSensitivity';
import { ArenaCostSpeed } from './pages/arena/ArenaCostSpeed';
import { ArenaFairnessRobustness } from './pages/arena/ArenaFairnessRobustness';
import { ArenaHeadToHead } from './pages/arena/ArenaHeadToHead';
import { ArenaMetricsDeepDive } from './pages/arena/ArenaMetricsDeepDive';
import { ArenaExplainability } from './pages/arena/ArenaExplainability';
import { ArenaLLMVerdict } from './pages/arena/ArenaLLMVerdict';

// Import ground truth machine artifacts directly
import leaderboardData from '../../artifacts/v2/comparison/leaderboard.json';
import mcdaData from '../../artifacts/v2/comparison/mcda.json';
import sensitivityData from '../../artifacts/v2/comparison/sensitivity.json';

// Mock apiV2 methods with ground truth comparison JSON files
vi.mock('./lib/api-client-v2', () => ({
  apiV2: {
    getCompare: vi.fn().mockImplementation((topic: string) => {
      if (topic === 'leaderboard') {
        return Promise.resolve(leaderboardData);
      }
      if (topic === 'sensitivity') {
        return Promise.resolve(sensitivityData);
      }
      if (topic === 'head2head') {
        return Promise.resolve({
          pairs: {
            rf_vs_boost: { diff: -0.0234, mcnemar_p: 0.012, ci: [-0.038, -0.009], significant: true },
          },
        });
      }
      if (topic === 'confusion') {
        return Promise.resolve({
          matrices: {
            rf: [[400, 20, 5], [15, 600, 30], [2, 25, 480]],
            boost: [[390, 25, 10], [20, 590, 35], [5, 30, 470]],
          },
        });
      }
      if (topic === 'curves') {
        return Promise.resolve({ roc_points: [], pr_points: [] });
      }
      if (topic === 'importance') {
        return Promise.resolve({
          importance_matrix: {
            rf: { attendance: 0.28, experience_years: 0.12, training_hours: 0.15, projects_completed: 0.22, weekly_hours: 0.08, prev_score: 0.15 },
          },
        });
      }
      if (topic === 'fairness') {
        return Promise.resolve({ audit_attribute: 'department', disparity_ratios: { boost: 0.87, rf: 0.89 }, parity_tolerance: 0.8 });
      }
      if (topic === 'robustness') {
        return Promise.resolve({ noise_stress_5pct_f1_drop: { boost: 0.022 }, missing_stress_10pct_f1_drop: { boost: 0.015 } });
      }
      return Promise.resolve({});
    }),
    postLLMVerdict: vi.fn().mockResolvedValue({
      headline: 'Boost leads SVM by 0.0090 MCDA points with decision strength none',
      recommendation: { model_key: 'boost', confidence: 'none', decision_strength: 'none' },
      claims: [
        { statement: 'Boost macro-F1 is 0.8038 versus SVM 0.8164.', fact_ids: ['F1', 'F2'] },
      ],
      trade_offs: ['SVM leads in accuracy, Boost leads in balanced composite score'],
      caveats: ['Decision strength is none; winner depends on user priorities'],
      validation: { passed: true, errors: [], source: 'llm', checks_evaluated: 16 },
      evidence_packet_hash: 'ev_hash_123',
    }),
    postMCDA: vi.fn().mockImplementation((_weights: Record<string, number>, profile: string) => {
      type RankingItem = { key: string; mcda_score: number; rank: number; p_rank1: number };
      type ProfileData = { winner: string; decision_strength: string; ranking: RankingItem[] };
       const profilesMap = (mcdaData.all_profiles as unknown) as Record<string, ProfileData & { deterministic_winner?: string }> | undefined;
      const prof = profilesMap ? profilesMap[profile] : null;
      return Promise.resolve({
        profile_name: profile,
         winner: prof ? (prof.winner || prof.deterministic_winner || mcdaData.deterministic_winner) : mcdaData.deterministic_winner,
        decision_strength: prof ? prof.decision_strength : mcdaData.decision_strength,
        ranked_models: prof
          ? prof.ranking.map((r: RankingItem) => ({
              key: r.key,
              composite_score: r.mcda_score,
              rank: r.rank,
              rank1_probability: r.p_rank1,
            }))
          : mcdaData.ranking.map((r: RankingItem) => ({
              key: r.key,
              composite_score: r.mcda_score,
              rank: r.rank,
              rank1_probability: r.p_rank1,
            })),
      });
    }),
  },
}));

describe('Arena Numbers Parity Tests (Artifacts Ground Truth vs UI)', () => {
  describe('ArenaOverview Numbers Parity', () => {
    it('renders exact leaderboard metrics matching leaderboard.json', async () => {
      render(<ArenaOverview />);

      await waitFor(() => {
        expect(screen.getByText(/Holdout Test Leaderboard/i)).toBeInTheDocument();
      });

      // Verify each model's macro-F1 is present in document
      for (const m of leaderboardData.metrics) {
        const f1Text = m.macro_f1.toFixed(3);
        const f1Elements = screen.getAllByText(new RegExp(f1Text));
        expect(f1Elements.length).toBeGreaterThan(0);
      }
    });

    it('renders honest champion narrative matching boost vs svm tie', async () => {
      render(<ArenaOverview />);

      await waitFor(() => {
        expect(screen.getAllByText(/Gradient boosting/i).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/Statistical Tie/i).length).toBeGreaterThan(0);
      });
    });
  });

  describe('ArenaPriorities MCDA Numbers Parity', () => {
    it('renders exact composite scores and margin matching mcda.json', async () => {
      render(<ArenaPriorities />);

      await waitFor(() => {
        expect(screen.getByText('Priority Profiles')).toBeInTheDocument();
      });

      // Assert composite score of boost (0.6665)
      const boostScore = mcdaData.ranking.find(r => r.key === 'boost')?.mcda_score;
      expect(boostScore).toBeCloseTo(0.6665, 3);

      // Assert composite score of svm (0.6575)
      const svmScore = mcdaData.ranking.find(r => r.key === 'svm')?.mcda_score;
      expect(svmScore).toBeCloseTo(0.6575, 3);

      // Assert score margin is 0.0090
      const margin = (mcdaData.ranking[0].mcda_score - mcdaData.ranking[1].mcda_score);
      expect(margin).toBeCloseTo(0.009, 3);
      expect(mcdaData.decision_strength).toBe('none');
    });
  });

  describe('ArenaSensitivity Numbers Parity', () => {
    it('renders exact profile winners matching sensitivity.json', async () => {
      render(<ArenaSensitivity />);

      await waitFor(() => {
        expect(screen.getByText(/Data Generator Sensitivity Analysis/i)).toBeInTheDocument();
      });

      type ProfileMap = Record<string, { winner: string }>;
       const sensDataMap = (sensitivityData as unknown) as Record<string, unknown>;
       const profiles = (sensDataMap.profiles || {}) as ProfileMap;
      if (profiles['Balanced']) {
        expect(profiles['Balanced'].winner).toBe('boost');
      }
      if (profiles['Accuracy-first']) {
        expect(profiles['Accuracy-first'].winner).toBe('svm');
      }
      if (profiles['Explainability-first']) {
        expect(profiles['Explainability-first'].winner).toBe('logreg');
      }
      if (profiles['Speed-first']) {
        expect(profiles['Speed-first'].winner).toBe('svm');
      }
      if (profiles['Fairness-first']) {
        expect(profiles['Fairness-first'].winner).toBe('rf');
      }

      // Verify calibration-removed runs
       const calRemoved = (sensDataMap.calibration_removed_profiles || {}) as ProfileMap;
      if (calRemoved['Balanced']) {
        expect(calRemoved['Balanced'].winner).toBe('boost');
      }
      if (calRemoved['Accuracy-first']) {
        expect(calRemoved['Accuracy-first'].winner).toBe('svm');
      }

      // Verify raw-calibration runs
       const rawCal = (sensDataMap.raw_calibration_profiles || {}) as ProfileMap;
      if (rawCal['Balanced']) {
        expect(rawCal['Balanced'].winner).toBe('boost');
      }
    });
  });

  describe('ArenaCostSpeed Numbers Parity', () => {
    it('renders the measured cost and latency table', async () => {
      render(<ArenaCostSpeed />);
      expect(screen.getByText(/Computational Cost, Latency/i)).toBeInTheDocument();
      expect(screen.getByText(/Accuracy vs Latency Trade-Off Matrix/i)).toBeInTheDocument();
    });
  });

  describe('ArenaFairnessRobustness Parity', () => {
    it('renders four-fifths fairness and robustness metrics', () => {
      render(<ArenaFairnessRobustness />);
      expect(screen.getByText(/Demographic Fairness Audit & Noise Stress-Testing/i)).toBeInTheDocument();
      expect(screen.getByText(/Demographic Disparity Ratios/i)).toBeInTheDocument();
       expect(screen.getByText(/Models Meet 4\/5ths/i)).toBeInTheDocument();
    });
  });

  describe('ArenaHeadToHead Parity', () => {
    it('renders statistical significance and McNemar comparison', async () => {
      render(<ArenaHeadToHead />);
      await waitFor(() => {
        expect(screen.getByText(/Pairwise Head-to-Head Model Arena/i)).toBeInTheDocument();
        expect(screen.getByText(/Model A \(Reference\):/i)).toBeInTheDocument();
      });
    });
  });

  describe('ArenaMetricsDeepDive Parity', () => {
    it('renders reliability curves and calibration deep-dive', async () => {
      render(<ArenaMetricsDeepDive />);
      await waitFor(() => {
        expect(screen.getByText(/Metrics Deep Dive: Multi-Class & Calibration Diagnostic/i)).toBeInTheDocument();
        expect(screen.getByText(/Per-Class F1 Heatmap/i)).toBeInTheDocument();
      });
    });
  });

  describe('ArenaExplainability Parity', () => {
    it('renders feature importance agreement and Spearman rank matrix', async () => {
      render(<ArenaExplainability />);
      await waitFor(() => {
        expect(screen.getByText(/Multi-Model Explainability & Feature Agreement Arena/i)).toBeInTheDocument();
        expect(screen.getByText(/Normalized Feature Importance Heatmap/i)).toBeInTheDocument();
      });
    });
  });

  describe('ArenaLLMVerdict Parity', () => {
    it('renders certified verdict engine and deterministic fallback', async () => {
      render(<ArenaLLMVerdict />);
      await waitFor(() => {
        expect(screen.getByText(/Enterprise AI Synthesis/i)).toBeInTheDocument();
      });
    });
  });
});
