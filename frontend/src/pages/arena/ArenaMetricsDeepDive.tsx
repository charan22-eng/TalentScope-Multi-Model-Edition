import { useState, useEffect } from 'react';
import { apiV2 } from '../../lib/api-client-v2';
import { ModelChip } from '../../components/ui/ModelChip';
import { Activity } from 'lucide-react';

interface ModelMetricsDeep {
  key: string;
  name: string;
  macro_f1?: number;
  f1_low?: number;
  f1_medium?: number;
  f1_high?: number;
  exact_rate?: number;
  adjacent_rate?: number;
  extreme_rate?: number;
  brier_score: number;
  ece: number;
  ovr_auc: number;
}

interface RawLeaderboardMetric {
  key: string;
  name?: string;
  label?: string;
  macro_f1?: number;
  f1_low?: number;
  f1_medium?: number;
  f1_high?: number;
  exact_rate?: number;
  exact_share?: number;
  adjacent_rate?: number;
  adjacent_share?: number;
  extreme_rate?: number;
  extreme_share?: number;
  brier_score?: number;
  brier?: number;
  ece?: number;
  ovr_auc?: number;
  roc_auc_ovr?: number;
  per_class?: Record<string, { f1?: number }>;
}

interface CurvePoint {
  key?: string;
  brier?: number;
  ece?: number;
  roc_auc_ovr?: number;
}

export function ArenaMetricsDeepDive() {
  const [metrics, setMetrics] = useState<ModelMetricsDeep[]>([]);

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const [lbData, curvesData] = await Promise.all([
          apiV2.getCompare('leaderboard') as unknown as Promise<{ metrics?: RawLeaderboardMetric[] }>,
          apiV2.getCompare('curves').catch(() => ({})) as unknown as Promise<{ metrics?: CurvePoint[] } | Record<string, CurvePoint>>,
        ]);

        const rawLeaderboardMetrics = lbData?.metrics || [];
        let curvesMap: Record<string, CurvePoint> = {};
        let curvesMetrics: CurvePoint[] | null = null;

        if (curvesData && typeof curvesData === 'object') {
          if ('metrics' in curvesData && Array.isArray(curvesData.metrics)) {
            curvesMetrics = curvesData.metrics as CurvePoint[];
            curvesMap = Object.fromEntries(curvesMetrics.map((c) => [c.key || '', c]));
          } else {
            curvesMap = curvesData as Record<string, CurvePoint>;
          }
        }

        const mapped: ModelMetricsDeep[] = rawLeaderboardMetrics.map((m) => {
          const perClass = m.per_class || {};
          const curveItem = curvesMap[m.key] || {};
          return {
            key: m.key,
            name: m.label || m.name || m.key.toUpperCase(),
            macro_f1: m.macro_f1,
            f1_low: m.f1_low ?? perClass.Low?.f1,
            f1_medium: m.f1_medium ?? perClass.Medium?.f1,
            f1_high: m.f1_high ?? perClass.High?.f1,
            exact_rate: m.exact_rate ?? m.exact_share,
            adjacent_rate: m.adjacent_rate ?? m.adjacent_share,
            extreme_rate: m.extreme_rate ?? m.extreme_share,
            brier_score: m.brier_score ?? m.brier ?? curveItem.brier ?? 0,
            ece: m.ece ?? curveItem.ece ?? 0,
            ovr_auc: m.ovr_auc ?? m.roc_auc_ovr ?? curveItem.roc_auc_ovr ?? 0,
          };
        });

        if (mapped.length > 0) {
          setMetrics(mapped);
        } else if (curvesMetrics && curvesMetrics.length > 0) {
          setMetrics(curvesMetrics as unknown as ModelMetricsDeep[]);
        }
      } catch (e) {
        console.warn('Error loading metrics breakdown for deep dive', e);
      }
    }
    fetchMetrics();
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
                    <ModelChip modelKey={m.key} size="sm" showChampionBadge={m.key === 'boost'} />
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', background: 'rgba(239, 68, 68, 0.08)' }}>
                    {m.f1_low === undefined ? '—' : m.f1_low.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', background: 'rgba(245, 158, 11, 0.08)' }}>
                    {m.f1_medium === undefined ? '—' : m.f1_medium.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', background: 'rgba(16, 185, 129, 0.08)' }}>
                    {m.f1_high === undefined ? '—' : m.f1_high.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700 }}>
                    {m.macro_f1 === undefined ? '—' : m.macro_f1.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {m.ovr_auc === undefined ? '—' : m.ovr_auc.toFixed(3)}
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
                    Exact: {m.exact_rate === undefined ? '—' : `${(m.exact_rate * 100).toFixed(1)}%`} | Extr: {m.extreme_rate === undefined ? '—' : `${(m.extreme_rate * 100).toFixed(2)}%`}
                  </span>
                </div>
                <div style={{ display: 'flex', height: '10px', borderRadius: '5px', overflow: 'hidden', background: 'var(--border-color)' }}>
                  <div style={{ width: `${(m.exact_rate || 0) * 100}%`, background: '#10b981' }} />
                  <div style={{ width: `${(m.adjacent_rate || 0) * 100}%`, background: '#f59e0b' }} />
                  <div style={{ width: `${(m.extreme_rate || 0) * 100}%`, background: '#ef4444' }} />
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
                  <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace', color: m.ece !== undefined && m.ece <= 0.025 ? '#10b981' : undefined }}>
                     {m.ece === undefined ? '—' : m.ece.toFixed(4)}
                  </td>
                  <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                     {m.brier_score === undefined ? '—' : m.brier_score.toFixed(3)}
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
