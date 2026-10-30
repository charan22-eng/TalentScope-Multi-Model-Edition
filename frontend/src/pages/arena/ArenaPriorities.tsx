import { useState, useEffect } from 'react';
import { apiV2, type MCDAResult } from '../../lib/api-client-v2';
import { ModelChip } from '../../components/ui/ModelChip';
import { Sliders, RotateCcw } from 'lucide-react';

const PRESETS: Record<string, Record<string, number>> = {
  Balanced: {
    macro_f1: 0.25,
    qwk: 0.10,
    calibration: 0.10,
    robustness: 0.10,
    fairness: 0.10,
    stability: 0.05,
    latency: 0.05,
    train_cost: 0.05,
    explainability: 0.20,
  },
  'High Accuracy': {
    macro_f1: 0.40,
    qwk: 0.20,
    calibration: 0.10,
    robustness: 0.10,
    fairness: 0.05,
    stability: 0.05,
    latency: 0.02,
    train_cost: 0.01,
    explainability: 0.07,
  },
  'Interpretability First': {
    macro_f1: 0.15,
    qwk: 0.05,
    calibration: 0.10,
    robustness: 0.05,
    fairness: 0.10,
    stability: 0.05,
    latency: 0.05,
    train_cost: 0.05,
    explainability: 0.40,
  },
  'Low Latency': {
    macro_f1: 0.15,
    qwk: 0.10,
    calibration: 0.05,
    robustness: 0.05,
    fairness: 0.05,
    stability: 0.05,
    latency: 0.35,
    train_cost: 0.15,
    explainability: 0.05,
  },
  'Fair & Robust': {
    macro_f1: 0.15,
    qwk: 0.10,
    calibration: 0.10,
    robustness: 0.20,
    fairness: 0.25,
    stability: 0.05,
    latency: 0.02,
    train_cost: 0.03,
    explainability: 0.10,
  },
};

const CRITERIA_LABELS: Record<string, string> = {
  macro_f1: 'Macro-F1 Score',
  qwk: 'Quadratic Weighted Kappa',
  calibration: 'Calibration Fidelity',
  robustness: 'Noise Robustness',
  fairness: 'Fairness Audit Ratio',
  stability: 'Prediction Stability',
  latency: 'Inference Speed (Low Latency)',
  train_cost: 'Training Cost',
  explainability: 'Explainability Architecture Tier',
};

export function ArenaPriorities() {
  const [activeProfile, setActiveProfile] = useState<string>('Balanced');
  const [weights, setWeights] = useState<Record<string, number>>(PRESETS.Balanced);
  const [result, setResult] = useState<MCDAResult | null>(null);
  const [loading, setLoading] = useState(false);

  // Evaluate MCDA server-side on weight changes
  const evaluateMCDA = async (w: Record<string, number>, profName: string) => {
    setLoading(true);
    try {
      const res = await apiV2.postMCDA(w, profName);
      setResult(res);
    } catch (e) {
      console.error('Failed to run server MCDA', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    evaluateMCDA(PRESETS.Balanced, 'Balanced');
  }, []);

  const handleSelectPreset = (presetName: string) => {
    setActiveProfile(presetName);
    const newWeights = PRESETS[presetName] || PRESETS.Balanced;
    setWeights(newWeights);
    evaluateMCDA(newWeights, presetName);
  };

  const handleWeightChange = (key: string, val: number) => {
    setActiveProfile('Custom');
    const updated = { ...weights, [key]: val };
    setWeights(updated);
  };

  const handleApplyCustom = () => {
    evaluateMCDA(weights, 'Custom');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Intro Header */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h2 style={{ margin: 0, fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sliders size={20} />
          Multi-Criteria Decision Analysis (MCDA) Priorities
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Configure enterprise tradeoffs across 9 performance, fairness, safety, and speed criteria.
          Evaluated via server-side Dirichlet weight perturbations (5,000 draws) to derive statistically grounded rank-1 probabilities.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(400px, 1.4fr)', gap: '1.5rem' }}>
        {/* Sliders Column */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Priority Profiles</h3>
            {activeProfile !== 'Balanced' && (
              <button
                type="button"
                onClick={() => handleSelectPreset('Balanced')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: 'none',
                  border: 'none',
                  color: 'var(--primary-text)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                <RotateCcw size={12} /> Reset to Balanced
              </button>
            )}
          </div>

          {/* Profile buttons */}
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
            {Object.keys(PRESETS).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => handleSelectPreset(p)}
                style={{
                  padding: '0.4rem 0.75rem',
                  borderRadius: 'var(--radius)',
                  border: `1px solid ${activeProfile === p ? 'var(--primary-color)' : 'var(--border-color)'}`,
                  background: activeProfile === p ? 'var(--primary-color)' : 'var(--bg-primary)',
                  color: activeProfile === p ? '#ffffff' : 'var(--text-primary)',
                  fontWeight: activeProfile === p ? 700 : 500,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                {p}
              </button>
            ))}
          </div>

          <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
            Criteria Weight Sliders ({activeProfile})
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {Object.entries(CRITERIA_LABELS).map(([k, label]) => {
              const currentWeight = weights[k] ?? 0.1;
              return (
                <div key={k}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                    <span>{label}</span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{(currentWeight * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={currentWeight}
                    onChange={e => handleWeightChange(k, parseFloat(e.target.value))}
                    onMouseUp={handleApplyCustom}
                    onTouchEnd={handleApplyCustom}
                    style={{ width: '100%' }}
                  />
                </div>
              );
            })}
          </div>

          <button
            type="button"
            onClick={handleApplyCustom}
            disabled={loading}
            style={{
              width: '100%',
              marginTop: '1.25rem',
              padding: '0.75rem',
              background: 'var(--primary-color)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius)',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Re-evaluating Server MCDA...' : 'Calculate Model Rankings'}
          </button>
        </div>

        {/* Results & Rank-1 Probabilities Column */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.2rem' }}>
                Winner: {result?.winner ? result.winner.toUpperCase() : '—'}
              </h3>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Rule: {result?.decision_rule || 'ADR-009 Multi-Criteria Decision Analysis'}
              </div>
            </div>

            {/* Decision Strength Badge */}
            {result && (
              <span
                style={{
                  fontSize: '0.8rem',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  background: result.decision_strength === 'clear' ? 'rgba(16, 185, 129, 0.15)' : result.decision_strength === 'marginal' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  border: `1px solid ${result.decision_strength === 'clear' ? '#10b981' : result.decision_strength === 'marginal' ? '#f59e0b' : '#ef4444'}`,
                  color: result.decision_strength === 'clear' ? '#10b981' : result.decision_strength === 'marginal' ? '#f59e0b' : '#ef4444',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
              >
                Decision Strength: {result.decision_strength}
              </span>
            )}
          </div>

          {/* Ranking Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Rank</th>
                  <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Model</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Score</th>
                  <th style={{ padding: '0.6rem', textAlign: 'left', width: '40%', borderBottom: '2px solid var(--border-color)' }}>
                    Rank-1 Probability (Dirichlet 5k)
                  </th>
                </tr>
              </thead>
              <tbody>
                {(result?.ranked_models || []).map((m) => {
                  const probPct = (m.rank1_probability * 100).toFixed(1);
                  return (
                    <tr
                      key={m.key}
                      style={{
                        borderBottom: '1px solid var(--border-color)',
                        background: m.key === result?.winner ? 'rgba(213, 94, 0, 0.08)' : undefined,
                      }}
                    >
                      <td style={{ padding: '0.6rem', fontWeight: 600 }}>#{m.rank}</td>
                      <td style={{ padding: '0.6rem' }}>
                        <ModelChip modelKey={m.key} size="sm" showChampionBadge={m.key === 'boost'} />
                      </td>
                      <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>
                        {m.composite_score.toFixed(3)}
                      </td>
                      <td style={{ padding: '0.6rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div style={{ flex: 1, height: '8px', background: 'var(--bg-primary)', borderRadius: '4px', overflow: 'hidden' }}>
                            <div
                              style={{
                                width: `${probPct}%`,
                                height: '100%',
                                background: m.key === result?.winner ? 'var(--accent-warm-action)' : 'var(--primary-action)',
                                transition: 'width 0.3s ease',
                              }}
                            />
                          </div>
                          <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', width: '45px', textAlign: 'right' }}>
                            {probPct}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
