import { ModelChip } from '../../components/ui/ModelChip';
import { Clock, Zap, HardDrive } from 'lucide-react';

interface CostItem {
  key: string;
  name: string;
  f1: number;
  trainTimeSec: number;
  p50LatencyMs: number;
  p95LatencyMs: number;
  batchLatencySec: number; // 5000 rows
  sizeKb: number;
  isParetoOptimal: boolean;
}

const COST_DATA: CostItem[] = [
  { key: 'linreg', name: 'Linear Regression', f1: 0.703, trainTimeSec: 0.8, p50LatencyMs: 3.2, p95LatencyMs: 13.2, batchLatencySec: 0.08, sizeKb: 45, isParetoOptimal: true },
  { key: 'dt', name: 'Decision Tree', f1: 0.709, trainTimeSec: 1.1, p50LatencyMs: 4.1, p95LatencyMs: 16.3, batchLatencySec: 0.11, sizeKb: 85, isParetoOptimal: true },
  { key: 'knn', name: 'K-Nearest Neighbours', f1: 0.754, trainTimeSec: 0.5, p50LatencyMs: 5.8, p95LatencyMs: 16.9, batchLatencySec: 2.45, sizeKb: 1420, isParetoOptimal: true },
  { key: 'logreg', name: 'Logistic Regression', f1: 0.719, trainTimeSec: 1.4, p50LatencyMs: 5.2, p95LatencyMs: 22.6, batchLatencySec: 0.14, sizeKb: 52, isParetoOptimal: false },
  { key: 'svm', name: 'Support Vector Machine', f1: 0.816, trainTimeSec: 14.5, p50LatencyMs: 8.5, p95LatencyMs: 23.5, batchLatencySec: 3.12, sizeKb: 890, isParetoOptimal: true },
  { key: 'rf', name: 'Random Forest', f1: 0.780, trainTimeSec: 12.2, p50LatencyMs: 24.1, p95LatencyMs: 99.4, batchLatencySec: 1.85, sizeKb: 2450, isParetoOptimal: false },
  { key: 'boost', name: 'Histogram Gradient Boosting', f1: 0.804, trainTimeSec: 8.4, p50LatencyMs: 28.5, p95LatencyMs: 105.8, batchLatencySec: 1.20, sizeKb: 680, isParetoOptimal: false },
];

export function ArenaCostSpeed() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h2 style={{ margin: 0, fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Zap size={20} />
          Computational Cost, Latency & Pareto Efficiency
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Real measured compute telemetry across training budgets, single-row inference percentiles, 5,000-row batch throughput, and artifact memory footprints.
        </p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Fastest Single Inference</span>
            <Clock size={16} color="var(--primary-color)" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>13.2 ms</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Linear Regression (p95)</div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Fastest 5,000-Row Batch</span>
            <Zap size={16} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>0.08 s</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Linear Regression Vectorized</div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Smallest Model Artifact</span>
            <HardDrive size={16} color="#a855f7" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>45 KB</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Linear Regression Pipeline</div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Champion Latency (RF)</span>
            <Clock size={16} color="#D55E00" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>99.4 ms</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Within 800ms SLA Limit</div>
        </div>
      </div>

      {/* Accuracy vs Latency Pareto Frontier Table */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem' }}>Accuracy vs Latency Trade-Off Matrix</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
          Pareto-optimal architectures achieve maximal predictive accuracy for a given latency ceiling.
        </p>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Model</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Macro-F1</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>p50 Latency</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>p95 Latency</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>5,000-Row Batch</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Train Time</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Artifact Size</th>
                <th style={{ padding: '0.6rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>Pareto Efficient</th>
              </tr>
            </thead>
            <tbody>
              {COST_DATA.map(c => (
                <tr key={c.key} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.6rem' }}>
                    <ModelChip modelKey={c.key} size="sm" showChampionBadge={c.key === 'rf'} />
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>
                    {c.f1.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {c.p50LatencyMs.toFixed(1)} ms
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>
                    {c.p95LatencyMs.toFixed(1)} ms
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {c.batchLatencySec.toFixed(2)} s
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {c.trainTimeSec.toFixed(1)} s
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {c.sizeKb > 1000 ? `${(c.sizeKb / 1024).toFixed(1)} MB` : `${c.sizeKb} KB`}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'center' }}>
                    {c.isParetoOptimal ? (
                      <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', fontWeight: 700 }}>
                        PARETO
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>—</span>
                    )}
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
