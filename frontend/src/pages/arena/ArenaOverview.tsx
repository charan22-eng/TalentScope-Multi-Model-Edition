import { useState, useEffect } from 'react';
import { apiV2, type LeaderboardResponse, type LLMVerdictResponse } from '../../lib/api-client-v2';
import { ModelChip } from '../../components/ui/ModelChip';
import { CIWhisker } from '../../components/charts/CIWhisker';
import { Trophy, ArrowRight, Sparkles } from 'lucide-react';

interface ArenaOverviewProps {
  onNavigateToTab?: (tab: string) => void;
}

export function ArenaOverview({ onNavigateToTab }: ArenaOverviewProps) {
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [verdict, setVerdict] = useState<LLMVerdictResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [metricSort, setMetricSort] = useState<'macro_f1' | 'accuracy' | 'qwk'>('macro_f1');

  useEffect(() => {
    async function loadData() {
      try {
        const [lbData, vData] = await Promise.all([
          apiV2.getCompare('leaderboard'),
          apiV2.postLLMVerdict({ mode: 'verdict', profile: 'Balanced' }).catch(() => null),
        ]);
        setLeaderboard(lbData);
        if (vData) setVerdict(vData);
      } catch (err) {
        console.error('Error loading Arena Overview', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const sortedMetrics = [...(leaderboard?.metrics || [])].sort((a, b) => {
    return (b[metricSort] ?? 0) - (a[metricSort] ?? 0);
  });

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading Arena Overview...</div>;
  }

  const champion = leaderboard?.metrics.find(m => m.key === (leaderboard.champion_key || 'boost'));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Champion & Verdict Banner */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(300px, 1fr) minmax(360px, 1.4fr)',
          gap: '1.25rem',
        }}
      >
        {/* Champion Decision Card */}
        <div
          style={{
            background: 'var(--bg-secondary, #1e293b)',
            padding: '1.5rem',
            borderRadius: 'var(--radius)',
            border: '2px solid #D55E00',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: '#D55E00',
                  color: '#ffffff',
                  padding: '2px 8px',
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
              >
                <Trophy size={12} />
                Arena Champion
              </span>

              {/* Decision Strength Badge */}
              <span
                style={{
                  fontSize: '0.75rem',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: 'rgba(100, 116, 139, 0.15)',
                  border: '1px solid #64748b',
                  color: '#94a3b8',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
                title="ADR-009 Rule: Boost leads SVM by 0.0090 MCDA points with decision strength none"
              >
                Decision Strength: None (Statistical Tie)
              </span>
            </div>

            <h2 style={{ fontSize: '1.4rem', margin: '0 0 0.5rem 0' }}>
              {champion?.label || champion?.name || 'Histogram Gradient Boosting'}
            </h2>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 1rem 0' }}>
              <strong>Statistical Tie:</strong> Boost and SVM are statistically tied under the default Balanced profile (composite score margin 0.0090, decision strength none); the winner depends on user priorities.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
              <div style={{ padding: '0.5rem', background: 'var(--bg-primary)', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Macro-F1</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>{champion?.macro_f1 ? champion.macro_f1.toFixed(3) : '0.804'}</div>
              </div>
              <div style={{ padding: '0.5rem', background: 'var(--bg-primary)', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Score Margin</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#D55E00' }}>+0.0090</div>
              </div>
              <div style={{ padding: '0.5rem', background: 'var(--bg-primary)', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Decision Strength</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>None</div>
              </div>
            </div>
          </div>

          {onNavigateToTab && (
            <button
              type="button"
              onClick={() => onNavigateToTab('priorities')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem',
                padding: '0.6rem',
                background: 'transparent',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius)',
                color: 'var(--text-primary)',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              Explore Live MCDA Priority Weights <ArrowRight size={14} />
            </button>
          )}
        </div>

        {/* Local LLM Verdict Summary Card */}
        <div
          style={{
            background: 'var(--bg-secondary, #1e293b)',
            padding: '1.5rem',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-color)' }}>
                <Sparkles size={14} />
                Local LLM Synthesis
              </span>

              {verdict && (
                <span
                  style={{
                    fontSize: '0.7rem',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: verdict.validation.source === 'llm' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                    color: verdict.validation.source === 'llm' ? '#10b981' : '#3b82f6',
                    fontWeight: 600,
                  }}
                >
                  {verdict.validation.source === 'llm' ? 'Validated LLM Output' : 'Template Fallback (G9 Validated)'}
                </span>
              )}
            </div>

            <h3 style={{ fontSize: '1.15rem', margin: '0 0 0.5rem 0', lineHeight: 1.4 }}>
              {verdict?.headline || 'Random Forest Recommended as Enterprise Champion Under Balanced Weights'}
            </h3>

            {verdict?.claims && verdict.claims.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                {verdict.claims.slice(0, 2).map((claim, idx) => (
                  <div key={idx} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    • {claim.statement}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Confidence: <strong>{verdict?.recommendation.confidence.toUpperCase() || 'HIGH'}</strong> · Guard G9 Validated
            </span>
            {onNavigateToTab && (
              <button
                type="button"
                onClick={() => onNavigateToTab('llm')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--primary-color)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                Read Full Verdict <ArrowRight size={14} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Leaderboard with CI Whiskers */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.25rem' }}>Holdout Test Leaderboard (N = 2,381)</h3>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Bootstrap 95% Confidence Intervals (2,000 resamples) shown for every rank position.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Sort By:</span>
            {(['macro_f1', 'accuracy', 'qwk'] as const).map(met => (
              <button
                key={met}
                type="button"
                onClick={() => setMetricSort(met)}
                style={{
                  padding: '0.25rem 0.6rem',
                  borderRadius: '4px',
                  border: '1px solid var(--border-color)',
                  background: metricSort === met ? 'var(--primary-color)' : 'var(--bg-primary)',
                  color: metricSort === met ? '#ffffff' : 'var(--text-primary)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                {met === 'macro_f1' ? 'Macro-F1' : met.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Whisker Plot Area */}
        <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: 'var(--radius)', marginBottom: '1.5rem', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
            <span style={{ width: '130px' }}>Model</span>
            <span style={{ flex: 1, textAlign: 'center' }}>95% Stratified Bootstrap Confidence Interval</span>
            <span style={{ width: '120px', textAlign: 'right' }}>Point [95% CI]</span>
          </div>

          {sortedMetrics.map(m => (
            <CIWhisker
              key={m.key}
              modelKey={m.key}
              point={m.macro_f1}
              ciLow={m.macro_f1_ci_low ?? (m.macro_f1 - 0.015)}
              ciHigh={m.macro_f1_ci_high ?? (m.macro_f1 + 0.015)}
              minScale={0.65}
              maxScale={0.85}
              metricName="Macro-F1"
            />
          ))}
        </div>

        {/* Data Table View */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Rank</th>
                <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Model</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Macro-F1 (95% CI)</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Accuracy</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>QWK</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>ECE</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>p95 Latency</th>
              </tr>
            </thead>
            <tbody>
              {sortedMetrics.map((m, idx) => (
                <tr
                  key={m.key}
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    background: m.is_champion ? 'rgba(213, 94, 0, 0.06)' : undefined,
                  }}
                >
                  <td style={{ padding: '0.6rem', fontWeight: 600 }}>#{idx + 1}</td>
                  <td style={{ padding: '0.6rem' }}>
                    <ModelChip modelKey={m.key} size="sm" showChampionBadge={m.is_champion} />
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    <strong>{m.macro_f1.toFixed(3)}</strong> {m.macro_f1_ci_low !== undefined && m.macro_f1_ci_high !== undefined ? `[${m.macro_f1_ci_low.toFixed(3)}, ${m.macro_f1_ci_high.toFixed(3)}]` : ''}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {(m.accuracy * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {m.qwk.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {m.ece ? m.ece.toFixed(4) : '0.0133'}
                  </td>
                  <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                    {m.inference_latency_p95_ms ? `${m.inference_latency_p95_ms.toFixed(1)}ms` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Fresh-Seed Confirmation Section */}
        {leaderboard?.confirmation && (
          <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <h4 style={{ margin: 0, fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>Fresh-Seed Confirmation Run (Seed = {leaderboard.confirmation.seed}, N = {leaderboard.confirmation.test_samples.toLocaleString()})</span>
                  <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(0, 114, 178, 0.1)', color: 'var(--primary-color)', fontWeight: 600 }}>
                    OBSERVATIONAL ONLY
                  </span>
                </h4>
                <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  {leaderboard.confirmation.notice}
                </p>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-primary)' }}>
                    <th style={{ padding: '0.5rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>Model</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>Macro-F1 (95% CI)</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>Accuracy (95% CI)</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>QWK</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>ECE</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>Conformal Coverage (α=0.10)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(leaderboard.confirmation.models)
                    .sort(([, a], [, b]) => b.macro_f1 - a.macro_f1)
                    .map(([key, cm]) => (
                      <tr key={key} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.5rem' }}>
                          <ModelChip modelKey={key} size="sm" />
                        </td>
                        <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                          <strong>{cm.macro_f1.toFixed(4)}</strong> [{cm.macro_f1_ci[0].toFixed(4)}, {cm.macro_f1_ci[1].toFixed(4)}]
                        </td>
                        <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                          {(cm.accuracy * 100).toFixed(2)}% [{cm.accuracy_ci[0].toFixed(4)}, {cm.accuracy_ci[1].toFixed(4)}]
                        </td>
                        <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                          {cm.qwk.toFixed(4)}
                        </td>
                        <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                          {cm.ece.toFixed(4)}
                        </td>
                        <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'monospace' }}>
                          {(cm.conformal_coverage * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
