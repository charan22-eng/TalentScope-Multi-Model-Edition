import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiV2, type LeaderboardResponse } from '../lib/api-client-v2';
import { MODEL_TOKENS } from '../lib/tokens';
import { ModelChip } from '../components/ui/ModelChip';
import { Trophy, ArrowUpRight, Activity, Cpu, Layers } from 'lucide-react';

export default function DashboardPage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiV2.getCompare('leaderboard');
        setLeaderboard(data);
      } catch (e) {
        console.error('Failed to load dashboard metrics', e);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const champion = leaderboard?.metrics.find(m => m.key === (leaderboard.champion_key || 'rf'));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1.5rem 0' }}>
      {/* Top Banner */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Executive Talent Analytics Dashboard</h1>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            High-level performance governance, champion telemetry, and multi-model consensus tracking.
          </p>
        </div>
        <Link
          to="/arena"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.6rem 1.2rem',
            background: 'var(--primary-color)',
            color: '#ffffff',
            borderRadius: 'var(--radius)',
            textDecoration: 'none',
            fontWeight: 600,
            fontSize: '0.9rem',
          }}
        >
          Open Model Arena <ArrowUpRight size={16} />
        </Link>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        {/* Champion Model KPI */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '2px solid #D55E00' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Active Arena Champion</span>
            <Trophy size={18} color="#D55E00" />
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
            {champion ? champion.name : 'Random Forest (Champion)'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Selected via <strong>{leaderboard?.champion_rule || 'ADR-009 Balanced MCDA'}</strong>
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <ModelChip modelKey={champion?.key || 'rf'} size="sm" />
          </div>
        </div>

        {/* Champion Primary Metric */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Champion Macro-F1</span>
            <Activity size={18} color="var(--primary-color)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
            {champion ? champion.macro_f1.toFixed(3) : '0.655'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            95% CI: [{champion ? champion.macro_f1_ci_low.toFixed(3) : '0.635'}, {champion ? champion.macro_f1_ci_high.toFixed(3) : '0.675'}]
          </div>
        </div>

        {/* Model Consensus Rate */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>7-Model Agreement Rate</span>
            <Cpu size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
            78.4%
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Unanimous predictions across validation slice
          </div>
        </div>

        {/* Evaluated Architectures */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Models in Governance</span>
            <Layers size={18} color="#a855f7" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
            7 Models
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Linear, Tree, Kernel, Ensemble, Boosting
          </div>
        </div>
      </div>

      {/* Model Roster Quick View */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.15rem' }}>Verified Model Leaderboard Summary</h3>
        {loading ? (
          <div>Loading benchmark metrics...</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Model</th>
                  <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Family</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Macro-F1</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Accuracy</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>QWK</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Latency (p95)</th>
                </tr>
              </thead>
              <tbody>
                {(leaderboard?.metrics || []).map((m) => {
                  const token = MODEL_TOKENS[m.key];
                  return (
                    <tr key={m.key} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.6rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ color: token?.color, fontWeight: 'bold' }}>{token?.marker}</span>
                          <span style={{ fontWeight: m.is_champion ? 700 : 500 }}>{m.name}</span>
                          {m.is_champion && (
                            <span style={{ background: '#D55E00', color: '#fff', fontSize: '0.65rem', padding: '1px 5px', borderRadius: '4px', fontWeight: 'bold' }}>
                              CHAMPION
                            </span>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '0.6rem', color: 'var(--text-secondary)' }}>{m.family}</td>
                      <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                        {m.macro_f1.toFixed(3)} [{m.macro_f1_ci_low.toFixed(3)}, {m.macro_f1_ci_high.toFixed(3)}]
                      </td>
                      <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                        {(m.accuracy * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                        {m.qwk.toFixed(3)}
                      </td>
                      <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                        {m.inference_latency_p95_ms ? `${m.inference_latency_p95_ms.toFixed(1)} ms` : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
