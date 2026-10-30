import { useState, useEffect } from 'react';
import { apiV2 } from '../../lib/api-client-v2';
import { ModelChip } from '../../components/ui/ModelChip';
import { DivergingBar } from '../../components/charts/DivergingBar';
import { GitCompare } from 'lucide-react';

const MODEL_KEYS = ['rf', 'boost', 'svm', 'knn', 'logreg', 'dt', 'linreg'];

interface PairwiseRecord {
  model_a?: string;
  model_b?: string;
  mcnemar_statistic?: number;
  stat?: number;
  p_value?: number;
  mcnemar_p?: number;
  raw_p?: number;
  holm_p_value?: number;
  holm_p?: number;
  discordant_a_b?: number;
  discordant_b_a?: number;
  b_discordant?: number;
  c_discordant?: number;
  is_significant?: boolean;
  significant?: boolean;
  diff?: number;
}

interface PairwiseData {
  pairs?: Record<string, PairwiseRecord>;
  pair_map?: Record<string, PairwiseRecord>;
}

interface ConfusionData {
  matrices?: Record<string, number[][]>;
  [key: string]: unknown;
}

interface LeaderboardMetric {
  key: string;
  macro_f1?: number;
  accuracy?: number;
}

interface LeaderboardData {
  metrics?: LeaderboardMetric[];
}

function formatPValue(p: number | undefined): string {
  if (p === undefined) return '—';
  if (p === 0) return '< 0.0001';
  if (p < 0.001) return p.toExponential(2);
  return p.toFixed(4);
}

function formatHolmP(p: number | undefined): string {
  if (p === undefined) return '—';
  if (p === 0) return '< 0.0001';
  if (p < 0.001) return p.toExponential(2);
  return p.toFixed(4);
}

export function ArenaHeadToHead() {
  const [modelA, setModelA] = useState<string>('rf');
  const [modelB, setModelB] = useState<string>('boost');
  const [pairwise, setPairwise] = useState<PairwiseData | null>(null);
  const [confusion, setConfusion] = useState<ConfusionData | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardData | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const [pw, cf, lb] = await Promise.all([
          apiV2.getCompare('head2head'),
          apiV2.getCompare('confusion'),
          apiV2.getCompare('leaderboard'),
        ]);
        setPairwise(pw as unknown as PairwiseData);
        setConfusion(cf as unknown as ConfusionData);
        setLeaderboard(lb as unknown as LeaderboardData);
      } catch (e) {
        console.error('Failed to load head-to-head comparison data', e);
      }
    }
    loadStats();
  }, []);

  const pairDict = pairwise?.pairs || pairwise?.pair_map || {};

  let pairStat: {
    mcnemar_statistic: number;
    p_value: number;
    holm_p_value: number;
    a_right_b_wrong: number;
    b_right_a_wrong: number;
    is_significant: boolean;
  } | null = null;

  if (modelA === modelB) {
    pairStat = {
      mcnemar_statistic: 0,
      p_value: 1.0,
      holm_p_value: 1.0,
      a_right_b_wrong: 0,
      b_right_a_wrong: 0,
      is_significant: false,
    };
  } else {
    const keyForward = `${modelA}_vs_${modelB}`;
    const keyReverse = `${modelB}_vs_${modelA}`;
    const recForward = pairDict[keyForward];
    const recReverse = pairDict[keyReverse];

    if (recForward) {
      const rawP = recForward.p_value ?? recForward.raw_p ?? recForward.mcnemar_p ?? 1;
      const holmP = recForward.holm_p_value ?? recForward.holm_p ?? rawP;
      const stat = recForward.mcnemar_statistic ?? recForward.stat ?? 0;
      const isSig = Boolean(recForward.is_significant ?? recForward.significant ?? (holmP < 0.05));
      const aRight = recForward.discordant_a_b ?? recForward.c_discordant ?? 0;
      const bRight = recForward.discordant_b_a ?? recForward.b_discordant ?? 0;

      pairStat = {
        mcnemar_statistic: stat,
        p_value: rawP,
        holm_p_value: holmP,
        a_right_b_wrong: aRight,
        b_right_a_wrong: bRight,
        is_significant: isSig,
      };
    } else if (recReverse) {
      const rawP = recReverse.p_value ?? recReverse.raw_p ?? recReverse.mcnemar_p ?? 1;
      const holmP = recReverse.holm_p_value ?? recReverse.holm_p ?? rawP;
      const stat = recReverse.mcnemar_statistic ?? recReverse.stat ?? 0;
      const isSig = Boolean(recReverse.is_significant ?? recReverse.significant ?? (holmP < 0.05));
      const aRight = recReverse.discordant_b_a ?? recReverse.b_discordant ?? 0;
      const bRight = recReverse.discordant_a_b ?? recReverse.c_discordant ?? 0;

      pairStat = {
        mcnemar_statistic: stat,
        p_value: rawP,
        holm_p_value: holmP,
        a_right_b_wrong: aRight,
        b_right_a_wrong: bRight,
        is_significant: isSig,
      };
    }
  }

  // Metric Advantage from Leaderboard (Model B - Model A)
  const metricsMap = (leaderboard?.metrics || []).reduce<Record<string, LeaderboardMetric>>((acc, m) => {
    acc[m.key] = m;
    return acc;
  }, {});

  const metricA = metricsMap[modelA];
  const metricB = metricsMap[modelB];

  const f1Advantage = (metricB?.macro_f1 !== undefined && metricA?.macro_f1 !== undefined)
    ? Number((metricB.macro_f1 - metricA.macro_f1).toFixed(4))
    : 0;

  const accAdvantage = (metricB?.accuracy !== undefined && metricA?.accuracy !== undefined)
    ? Number((metricB.accuracy - metricA.accuracy).toFixed(4))
    : 0;

  // Confusion matrices
  const matrixA = confusion?.matrices?.[modelA] ||
    (confusion as unknown as Record<string, { matrix?: number[][] }>)?.[modelA]?.matrix ||
    [];
  const matrixB = confusion?.matrices?.[modelB] ||
    (confusion as unknown as Record<string, { matrix?: number[][] }>)?.[modelB]?.matrix ||
    [];

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
          {modelA === modelB ? (
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', fontWeight: 700 }}>
              Identical Models (p = 1.00)
            </span>
          ) : pairStat?.is_significant ? (
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
              {formatPValue(pairStat?.p_value)}
            </div>
          </div>
          <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: '4px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Holm Adjusted p-value</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
              {formatHolmP(pairStat?.holm_p_value)}
            </div>
          </div>
          <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: '4px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{modelA.toUpperCase()} Right / {modelB.toUpperCase()} Wrong</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
              {pairStat?.a_right_b_wrong !== undefined ? `${pairStat.a_right_b_wrong} cases` : '—'}
            </div>
          </div>
          <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: '4px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{modelB.toUpperCase()} Right / {modelA.toUpperCase()} Wrong</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
              {pairStat?.b_right_a_wrong !== undefined ? `${pairStat.b_right_a_wrong} cases` : '—'}
            </div>
          </div>
        </div>

        {/* Diverging Deltas */}
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.4rem' }}>Metric Advantage (Δ = Model B − Model A)</h4>
          <DivergingBar
            label="Macro-F1 Advantage"
            value={f1Advantage}
            leftLabel={modelA.toUpperCase()}
            rightLabel={modelB.toUpperCase()}
            maxAbsValue={0.1}
          />
          <DivergingBar
            label="Holdout Accuracy Advantage"
            value={accAdvantage}
            leftLabel={modelA.toUpperCase()}
            rightLabel={modelB.toUpperCase()}
            maxAbsValue={0.1}
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
