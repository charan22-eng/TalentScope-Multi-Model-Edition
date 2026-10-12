import { useState } from 'react';
import { ModelChip } from '../components/ui/ModelChip';
import { AlertTriangle, Play, RefreshCw, CheckCircle2 } from 'lucide-react';

const MODEL_KEYS = ['rf', 'boost', 'dt', 'knn', 'svm', 'logreg', 'linreg'];

export default function ModelLabPage() {
  const [targetModel, setTargetModel] = useState<string>('rf');
  const [profile, setProfile] = useState<'fast' | 'standard'>('fast');
  const [hyperparamTuning, setHyperparamTuning] = useState<boolean>(true);
  const [training, setTraining] = useState<boolean>(false);
  const [tunedResult, setTunedResult] = useState<{
    model: string;
    macroF1: number;
    accuracy: number;
    cvStd: number;
    trainTime: number;
  } | null>(null);

  const handleSimulateRetrain = () => {
    setTraining(true);
    setTunedResult(null);
    setTimeout(() => {
      // Simulate server-side fast tuning run adhering to inner CV protocol
      const baselineF1: Record<string, number> = {
        rf: 0.655,
        boost: 0.651,
        dt: 0.612,
        knn: 0.601,
        svm: 0.628,
        logreg: 0.589,
        linreg: 0.582,
      };

      const base = baselineF1[targetModel] || 0.600;
      // Slight delta representing candidate exploration
      const delta = (Math.random() * 0.008) - 0.003;
      setTunedResult({
        model: targetModel,
        macroF1: Number((base + delta).toFixed(3)),
        accuracy: Number((0.68 + delta).toFixed(3)),
        cvStd: 0.012,
        trainTime: profile === 'fast' ? 1.4 : 8.5,
      });
      setTraining(false);
    }, 1200);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1.5rem 0' }}>
      {/* Header Banner */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Model Lab: Architecture Tuning Sandbox</h1>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Experiment with hyperparameters, scaling pipelines, and tuning budgets without modifying locked production weights.
            </p>
          </div>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.35rem 0.75rem',
              borderRadius: '9999px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid var(--danger-color)',
              color: 'var(--danger-color)',
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            <AlertTriangle size={14} />
            Experimental · Not Deployed
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Tuning Configuration */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.15rem', marginTop: 0, marginBottom: '1rem' }}>Configuration & Protocol</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem' }}>
                Select Architecture to Tune:
              </label>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {MODEL_KEYS.map((k) => (
                  <ModelChip
                    key={k}
                    modelKey={k}
                    active={targetModel === k}
                    onClick={() => setTargetModel(k)}
                    showChampionBadge={false}
                  />
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem' }}>
                Tuning Profile (Budget):
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setProfile('fast')}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    borderRadius: 'var(--radius)',
                    border: `1px solid ${profile === 'fast' ? 'var(--primary-color)' : 'var(--border-color)'}`,
                    background: profile === 'fast' ? 'var(--primary-color)' : 'var(--bg-primary)',
                    color: profile === 'fast' ? '#ffffff' : 'var(--text-primary)',
                    cursor: 'pointer',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                  }}
                >
                  Fast (5 iterations, 5-fold CV)
                </button>
                <button
                  type="button"
                  onClick={() => setProfile('standard')}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    borderRadius: 'var(--radius)',
                    border: `1px solid ${profile === 'standard' ? 'var(--primary-color)' : 'var(--border-color)'}`,
                    background: profile === 'standard' ? 'var(--primary-color)' : 'var(--bg-primary)',
                    color: profile === 'standard' ? '#ffffff' : 'var(--text-primary)',
                    cursor: 'pointer',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                  }}
                >
                  Standard (20 iterations, 5-fold CV)
                </button>
              </div>
            </div>

            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={hyperparamTuning}
                  onChange={e => setHyperparamTuning(e.target.checked)}
                />
                Enable Random Search Inner Stratified CV (scoring: macro-F1)
              </label>
            </div>

            <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <strong>Governance Lock Notice:</strong> Tuning strictly executes on the development split (60% train).
              Locked test holdout (20%) is isolated under Guard G6 and cannot be touched by sandbox runs.
            </div>

            <button
              type="button"
              onClick={handleSimulateRetrain}
              disabled={training}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                marginTop: '0.5rem',
                padding: '0.8rem',
                background: 'var(--primary-color)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius)',
                fontWeight: 700,
                cursor: training ? 'not-allowed' : 'pointer',
              }}
            >
              {training ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
              {training ? 'Training Model & Computing CV...' : `Launch Experimental Tuning (${targetModel.toUpperCase()})`}
            </button>
          </div>
        </div>

        {/* Results Comparison */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.15rem', marginTop: 0, marginBottom: '1rem' }}>Benchmark vs Sandbox Comparison</h2>

          {tunedResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: 600 }}>
                <CheckCircle2 size={18} />
                Experimental Run Complete ({tunedResult.trainTime}s runtime)
              </div>

              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '2px solid var(--border-color)' }}>Metric</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '2px solid var(--border-color)' }}>Frozen Baseline</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '2px solid var(--border-color)' }}>Experimental</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '2px solid var(--border-color)' }}>Delta</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.5rem', fontWeight: 600 }}>Macro-F1 (CV)</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>0.655</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700 }}>
                      {tunedResult.macroF1.toFixed(3)}
                    </td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace', color: tunedResult.macroF1 >= 0.655 ? '#10b981' : '#ef4444' }}>
                      {(tunedResult.macroF1 - 0.655) >= 0 ? `+${(tunedResult.macroF1 - 0.655).toFixed(3)}` : (tunedResult.macroF1 - 0.655).toFixed(3)}
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.5rem', fontWeight: 600 }}>Accuracy</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>68.2%</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                      {(tunedResult.accuracy * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                      {((tunedResult.accuracy - 0.682) * 100).toFixed(1)}%
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.5rem', fontWeight: 600 }}>Inner CV Std</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>±0.014</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>±0.012</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>-0.002</td>
                  </tr>
                </tbody>
              </table>

              <div style={{ padding: '0.85rem', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', borderRadius: 'var(--radius)', fontSize: '0.8rem' }}>
                <strong>Promote to Candidate:</strong> To deploy an experimental model to production, an Admin must submit a Retrain Proposal under governed MLOps pipeline (Stage L4).
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-secondary)' }}>
              Select a target architecture and click "Launch Experimental Tuning" to evaluate performance.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
