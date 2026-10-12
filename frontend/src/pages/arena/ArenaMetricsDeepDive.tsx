import { useState, useEffect } from 'react';
import { apiV2 } from '../../lib/api-client-v2';
import { ModelChip } from '../../components/ui/ModelChip';
import { Activity } from 'lucide-react';

interface ModelMetricsDeep {
  key: string;
  name: string;
  macro_f1: number;
  f1_low: number;
  f1_medium: number;
  f1_high: number;
  exact_rate: number;
  adjacent_rate: number;
  extreme_rate: number;
  brier_score: number;
  ece: number;
  ovr_auc: number;
}

const SAMPLE_DEEP_METRICS: ModelMetricsDeep[] = [
  { key: 'rf', name: 'Random Forest', macro_f1: 0.780, f1_low: 0.812, f1_medium: 0.724, f1_high: 0.805, exact_rate: 0.777, adjacent_rate: 0.221, extreme_rate: 0.002, brier_score: 0.285, ece: 0.0133, ovr_auc: 0.912 },
  { key: 'boost', name: 'Histogram Gradient Boosting', macro_f1: 0.804, f1_low: 0.835, f1_medium: 0.751, f1_high: 0.825, exact_rate: 0.801, adjacent_rate: 0.194, extreme_rate: 0.005, brier_score: 0.292, ece: 0.0904, ovr_auc: 0.924 },
  { key: 'svm', name: 'Support Vector Machine', macro_f1: 0.816, f1_low: 0.842, f1_medium: 0.768, f1_high: 0.839, exact_rate: 0.815, adjacent_rate: 0.181, extreme_rate: 0.004, brier_score: 0.274, ece: 0.0270, ovr_auc: 0.931 },
  { key: 'knn', name: 'K-Nearest Neighbours', macro_f1: 0.754, f1_low: 0.784, f1_medium: 0.695, f1_high: 0.784, exact_rate: 0.752, adjacent_rate: 0.241, extreme_rate: 0.007, brier_score: 0.320, ece: 0.0246, ovr_auc: 0.890 },
  { key: 'logreg', name: 'Logistic Regression', macro_f1: 0.719, f1_low: 0.751, f1_medium: 0.652, f1_high: 0.753, exact_rate: 0.715, adjacent_rate: 0.274, extreme_rate: 0.011, brier_score: 0.362, ece: 0.1246, ovr_auc: 0.865 },
  { key: 'dt', name: 'Decision Tree', macro_f1: 0.709, f1_low: 0.742, f1_medium: 0.640, f1_high: 0.746, exact_rate: 0.708, adjacent_rate: 0.278, extreme_rate: 0.014, brier_score: 0.380, ece: 0.0342, ovr_auc: 0.842 },
  { key: 'linreg', name: 'Linear Regression (ScoreToBand)', macro_f1: 0.703, f1_low: 0.738, f1_medium: 0.635, f1_high: 0.736, exact_rate: 0.701, adjacent_rate: 0.288, extreme_rate: 0.011, brier_score: 0.370, ece: 0.0213, ovr_auc: 0.850 },
];

export function ArenaMetricsDeepDive() {
  const [metrics, setMetrics] = useState<ModelMetricsDeep[]>(SAMPLE_DEEP_METRICS);

  useEffect(() => {
    async function fetchCurves() {
      try {
        const curves = await apiV2.getCompare('curves');
        if (curves?.metrics) {
          setMetrics(curves.metrics);
        }
      } catch (e) {
        console.warn('Using default metrics breakdown for deep dive', e);
      }
    }
    fetchCurves();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h2 style={{ margin: 0, fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={20} />
          Metrics Deep Dive: Multi-Class & Calibration Diagnostic
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Examine per-class performance asymmetries, calibration error (ECE), and ordinal error distribution across all 7 models.
        </p>
      </div>

      {/* Per-Class F1 Heatmap Table */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem' }}>Per-Class F1 Heatmap (Model × Class)</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
          Highlights performance disparities between boundary classes (Low, High) and intermediate transition states (Medium).
        </p>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Model</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>F1: Low</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>F1: Medium</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>F1: High</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Macro-F1</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>OvR AUC</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map(m => (
                <tr key={m.key} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.6rem' }}>
                    <ModelChip modelKey={m.key} size="sm" showChampionBadge={m.key === 'rf'} />
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', background: 'rgba(239, 68, 68, 0.08)' }}>
                    {m.f1_low.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', background: 'rgba(245, 158, 11, 0.08)' }}>
                    {m.f1_medium.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', background: 'rgba(16, 185, 129, 0.08)' }}>
                    {m.f1_high.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700 }}>
                    {m.macro_f1.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {m.ovr_auc.toFixed(3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ordinal Errors Breakdown & Calibration Diagnostics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
        {/* Ordinal Error Breakdown */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem' }}>Ordinal Error Structure</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
            In high-stakes talent mobility, an extreme 2-band error (e.g. predicting High for a true Low candidate) is severe, whereas adjacent errors (Low vs Medium) reflect natural boundary noise.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {metrics.map(m => (
              <div key={m.key} style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                  <span>{m.name}</span>
                  <span style={{ fontFamily: 'monospace' }}>
                    Exact: {(m.exact_rate * 100).toFixed(1)}% | Extr: {(m.extreme_rate * 100).toFixed(2)}%
                  </span>
                </div>
                <div style={{ display: 'flex', height: '10px', borderRadius: '5px', overflow: 'hidden', background: 'var(--border-color)' }}>
                  <div style={{ width: `${m.exact_rate * 100}%`, background: '#10b981' }} title={`Exact: ${(m.exact_rate * 100).toFixed(1)}%`} />
                  <div style={{ width: `${m.adjacent_rate * 100}%`, background: '#f59e0b' }} title={`Adjacent Error (1 band): ${(m.adjacent_rate * 100).toFixed(1)}%`} />
                  <div style={{ width: `${m.extreme_rate * 100}%`, background: '#ef4444' }} title={`Extreme Error (2 bands): ${(m.extreme_rate * 100).toFixed(2)}%`} />
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', background: '#10b981', borderRadius: '50%' }} /> Exact Match
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', background: '#f59e0b', borderRadius: '50%' }} /> Adjacent Error (1 band)
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', background: '#ef4444', borderRadius: '50%' }} /> Extreme Error (2 bands)
            </span>
          </div>
        </div>

        {/* Calibration & Brier Score */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem' }}>Probability Calibration Fidelity</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
            Expected Calibration Error (ECE) and Brier scores evaluated on held-out calibration test split.
          </p>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>Model</th>
                <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>ECE</th>
                <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>Brier</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map(m => (
                <tr key={m.key} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.5rem', fontWeight: 500 }}>{m.name}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace', color: m.ece <= 0.025 ? '#10b981' : undefined }}>
                    {m.ece.toFixed(4)}
                  </td>
                  <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {m.brier_score.toFixed(3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
