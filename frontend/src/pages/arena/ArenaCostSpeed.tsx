import { useEffect, useState } from 'react';
import { apiV2, type LeaderboardResponse } from '../../lib/api-client-v2';
import { ModelChip } from '../../components/ui/ModelChip';
import { Clock, Zap, HardDrive } from 'lucide-react';

interface CostItem {
  key: string;
  name: string;
  f1: number;
  trainTimeSec: number;
  p50LatencyMs: number;
  p95LatencyMs: number;
  batchLatencySec: number;
  sizeKb: number;
  isParetoOptimal: boolean;
}

export function ArenaCostSpeed() {
  const [costData, setCostData] = useState<CostItem[]>([]);

  useEffect(() => {
    void apiV2.getCompare('leaderboard').then((raw) => {
      const leaderboard = raw as unknown as LeaderboardResponse;
      const items = leaderboard.metrics.map((metric) => ({
        key: metric.key,
        name: metric.name,
        f1: metric.macro_f1,
        trainTimeSec: metric.training_time_sec || 0,
        p50LatencyMs: metric.inference_latency_p50_ms || 0,
        p95LatencyMs: metric.inference_latency_p95_ms || 0,
        batchLatencySec: (metric.batch_latency_ms || 0) / 1000,
        sizeKb: metric.model_size_kb || 0,
        isParetoOptimal: false,
      }));
      const paretoKeys = items
        .filter((item) => !items.some((other) => other.key !== item.key && other.f1 >= item.f1 && other.p95LatencyMs <= item.p95LatencyMs && (other.f1 > item.f1 || other.p95LatencyMs < item.p95LatencyMs)))
        .map((item) => item.key);
      setCostData(items.map((item) => ({ ...item, isParetoOptimal: paretoKeys.includes(item.key) })));
    }).catch(() => setCostData([]));
  }, []);

  const fastest = costData.filter((item) => item.p95LatencyMs > 0).sort((a, b) => a.p95LatencyMs - b.p95LatencyMs)[0];
  const fastestBatch = costData.filter((item) => item.batchLatencySec > 0).sort((a, b) => a.batchLatencySec - b.batchLatencySec)[0];
  const smallest = costData.filter((item) => item.sizeKb > 0).sort((a, b) => a.sizeKb - b.sizeKb)[0];
  const champion = costData.find((item) => item.key === 'boost');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h2 style={{ margin: 0, fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Zap size={20} />Computational Cost, Latency &amp; Pareto Efficiency</h2>
        <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Measured telemetry loaded from the locked leaderboard artifact.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}><Clock size={16} /><div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{fastest ? `${fastest.p95LatencyMs.toFixed(1)} ms` : '—'}</div><div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{fastest ? `${fastest.name} (p95)` : 'Loading benchmark'}</div></div>
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}><Zap size={16} /><div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>{fastestBatch ? `${fastestBatch.batchLatencySec.toFixed(2)} s` : '—'}</div><div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{fastestBatch ? `${fastestBatch.name} batch` : 'Loading benchmark'}</div></div>
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}><HardDrive size={16} /><div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{smallest ? `${smallest.sizeKb.toFixed(0)} KB` : '—'}</div><div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{smallest ? smallest.name : 'Loading benchmark'}</div></div>
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}><Clock size={16} /><div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{champion ? `${champion.p95LatencyMs.toFixed(1)} ms` : '—'}</div><div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Boost champion p95 latency</div></div>
      </div>

      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', overflowX: 'auto' }}>
        <h3 style={{ margin: '0 0 1rem', fontSize: '1.15rem' }}>Accuracy vs Latency Trade-Off Matrix</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead><tr>{['Model', 'Macro-F1', 'p50', 'p95', '5,000-row batch', 'Train time', 'Artifact size', 'Pareto'].map((label) => <th key={label} style={{ padding: '0.6rem', textAlign: label === 'Model' ? 'left' : 'right', borderBottom: '2px solid var(--border-color)' }}>{label}</th>)}</tr></thead>
          <tbody>{costData.map((item) => <tr key={item.key} style={{ borderBottom: '1px solid var(--border-color)' }}>
            <td style={{ padding: '0.6rem' }}><ModelChip modelKey={item.key} size="sm" showChampionBadge={item.key === 'boost'} /></td>
            <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{item.f1.toFixed(3)}</td>
            <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{item.p50LatencyMs.toFixed(1)} ms</td>
            <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{item.p95LatencyMs.toFixed(1)} ms</td>
            <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{item.batchLatencySec.toFixed(2)} s</td>
            <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{item.trainTimeSec.toFixed(2)} s</td>
            <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{item.sizeKb.toFixed(0)} KB</td>
            <td style={{ padding: '0.6rem', textAlign: 'center' }}>{item.isParetoOptimal ? 'PARETO' : '—'}</td>
          </tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
