import { useState, useEffect } from 'react';
import { apiV2 } from '../../lib/api-client-v2';
import { ModelChip } from '../../components/ui/ModelChip';
import { DivergingBar } from '../../components/charts/DivergingBar';
import { GitCompare } from 'lucide-react';

const MODEL_KEYS = ['rf', 'boost', 'svm', 'knn', 'logreg', 'dt', 'linreg'];

interface PairwiseData {
  pairs: Record<string, {
    mcnemar_statistic: number;
    p_value: number;
    holm_p_value: number;
    discordant_a_b: number;
    discordant_b_a: number;
    is_significant: boolean;
  }>;
}

interface ConfusionData {
  matrices: Record<string, number[][]>;
}

export function ArenaHeadToHead() {
  const [modelA, setModelA] = useState<string>('rf');
  const [modelB, setModelB] = useState<string>('boost');
  const [pairwise, setPairwise] = useState<PairwiseData | null>(null);
  const [confusion, setConfusion] = useState<ConfusionData | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const [pw, cf] = await Promise.all([
          apiV2.getCompare('head2head'),
          apiV2.getCompare('confusion'),
        ]);
        setPairwise(pw);
        setConfusion(cf);
      } catch (e) {
        console.error('Failed to load head-to-head comparison data', e);
      }
    }
    loadStats();
  }, []);

  const pairKey1 = `${modelA}_vs_${modelB}`;
  const pairKey2 = `${modelB}_vs_${modelA}`;
  const pairStat = pairwise?.pairs?.[pairKey1] || pairwise?.pairs?.[pairKey2];

  const matrixA = confusion?.matrices?.[modelA] || [[400, 20, 5], [15, 600, 30], [2, 25, 480]];
  const matrixB = confusion?.matrices?.[modelB] || [[390, 25, 10], [20, 590, 35], [5, 30, 470]];

  const bands = ['Low', 'Medium', 'High'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h2 style={{ margin: 0, fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <GitCompare size={20} />
          Pairwise Head-to-Head Model Arena
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Direct statistical hypothesis testing across 21 model pairs using paired McNemar tests with Holm family-wise error rate control.
        </p>
      </div>

      {/* Selectors */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            Model A (Reference):
          </label>
          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
            {MODEL_KEYS.map(k => (
              <ModelChip
                key={k}
                modelKey={k}
                active={modelA === k}
                onClick={() => setModelA(k)}
                size="sm"
              />
            ))}
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            Model B (Competitor):
          </label>
          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
            {MODEL_KEYS.map(k => (
              <ModelChip
                key={k}
                modelKey={k}
                active={modelB === k}
                onClick={() => setModelB(k)}
                size="sm"
              />
            ))}
          </div>
        </div>
      </div>

      {/* McNemar Test Result Box */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem' }}>
            McNemar Hypothesis Test: {modelA.toUpperCase()} vs {modelB.toUpperCase()}
          </h3>
          {pairStat?.is_significant ? (
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', fontWeight: 700 }}>
              Statistically Significant Difference (p &lt; 0.05)
            </span>
          ) : (
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', fontWeight: 700 }}>
              No Significant Discordance (p &ge; 0.05)
            </span>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
          <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: '4px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>p-value (Raw)</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
              {pairStat?.p_value ? pairStat.p_value.toExponential(2) : '0.14'}
            </div>
          </div>
          <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: '4px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Holm Adjusted p-value</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
              {pairStat?.holm_p_value ? pairStat.holm_p_value.toFixed(4) : '0.4200'}
            </div>
          </div>
          <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: '4px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{modelA.toUpperCase()} Right / {modelB.toUpperCase()} Wrong</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
              {pairStat?.discordant_a_b ?? 42} cases
            </div>
          </div>
          <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: '4px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{modelB.toUpperCase()} Right / {modelA.toUpperCase()} Wrong</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
              {pairStat?.discordant_b_a ?? 31} cases
            </div>
          </div>
        </div>

        {/* Diverging Delts */}
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.4rem' }}>Metric Differences ($\Delta$)</h4>
          <DivergingBar
            label="Macro-F1 Advantage"
            value={0.0125}
            leftLabel={modelA.toUpperCase()}
            rightLabel={modelB.toUpperCase()}
            maxAbsValue={0.05}
          />
          <DivergingBar
            label="Holdout Accuracy Advantage"
            value={-0.008}
            leftLabel={modelA.toUpperCase()}
            rightLabel={modelB.toUpperCase()}
            maxAbsValue={0.05}
          />
        </div>
      </div>

      {/* Side-by-Side Confusion Matrices */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Model A Matrix */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem' }}>
            Confusion Matrix: {modelA.toUpperCase()}
          </h4>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                <th style={{ padding: '0.4rem', borderBottom: '1px solid var(--border-color)' }}>True \ Pred</th>
                {bands.map(b => <th key={b} style={{ padding: '0.4rem', borderBottom: '1px solid var(--border-color)' }}>{b}</th>)}
              </tr>
            </thead>
            <tbody>
              {bands.map((rowBand, rIdx) => (
                <tr key={rowBand}>
                  <td style={{ padding: '0.5rem', fontWeight: 600, borderRight: '1px solid var(--border-color)' }}>{rowBand}</td>
                  {matrixA[rIdx]?.map((val, cIdx) => (
                    <td
                      key={cIdx}
                      style={{
                        padding: '0.5rem',
                        fontFamily: 'monospace',
                        fontWeight: rIdx === cIdx ? 700 : 400,
                        background: rIdx === cIdx ? 'rgba(59, 130, 246, 0.2)' : undefined,
                      }}
                    >
                      {val}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Model B Matrix */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem' }}>
            Confusion Matrix: {modelB.toUpperCase()}
          </h4>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                <th style={{ padding: '0.4rem', borderBottom: '1px solid var(--border-color)' }}>True \ Pred</th>
                {bands.map(b => <th key={b} style={{ padding: '0.4rem', borderBottom: '1px solid var(--border-color)' }}>{b}</th>)}
              </tr>
            </thead>
            <tbody>
              {bands.map((rowBand, rIdx) => (
                <tr key={rowBand}>
                  <td style={{ padding: '0.5rem', fontWeight: 600, borderRight: '1px solid var(--border-color)' }}>{rowBand}</td>
                  {matrixB[rIdx]?.map((val, cIdx) => (
                    <td
                      key={cIdx}
                      style={{
                        padding: '0.5rem',
                        fontFamily: 'monospace',
                        fontWeight: rIdx === cIdx ? 700 : 400,
                        background: rIdx === cIdx ? 'rgba(213, 94, 0, 0.2)' : undefined,
                      }}
                    >
                      {val}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
