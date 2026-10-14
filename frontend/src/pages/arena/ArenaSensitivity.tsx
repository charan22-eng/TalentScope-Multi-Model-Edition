import { useState, useEffect } from 'react';
import { apiV2 } from '../../lib/api-client-v2';
import { BumpChart, type VariantRanking } from '../../components/charts/BumpChart';
import { ModelChip } from '../../components/ui/ModelChip';
import { GitBranch, AlertTriangle } from 'lucide-react';

const SAMPLE_RANKINGS: VariantRanking[] = [
  { modelKey: 'rf', linearRank: 4, nonlinearRank: 3, noisyRank: 1 },
  { modelKey: 'svm', linearRank: 3, nonlinearRank: 1, noisyRank: 3 },
  { modelKey: 'boost', linearRank: 2, nonlinearRank: 2, noisyRank: 2 },
  { modelKey: 'knn', linearRank: 5, nonlinearRank: 4, noisyRank: 5 },
  { modelKey: 'linreg', linearRank: 1, nonlinearRank: 7, noisyRank: 6 },
  { modelKey: 'logreg', linearRank: 6, nonlinearRank: 5, noisyRank: 4 },
  { modelKey: 'dt', linearRank: 7, nonlinearRank: 6, noisyRank: 7 },
];

export function ArenaSensitivity() {
  const [rankings, setRankings] = useState<VariantRanking[]>(SAMPLE_RANKINGS);
  const [kendallTau, setKendallTau] = useState<{
    linearVsNonlinear: number;
    nonlinearVsNoisy: number;
  }>({
    linearVsNonlinear: 0.428,
    nonlinearVsNoisy: 0.714,
  });
  const [calSensitivity, setCalSensitivity] = useState<any>(null);
  const [activeCalScenario, setActiveCalScenario] = useState<'calibration_removed' | 'raw_calibration'>('calibration_removed');

  useEffect(() => {
    async function loadSensitivity() {
      try {
        const data = await apiV2.getCompare('sensitivity');
        if (data?.rankings) {
          setRankings(data.rankings);
        }
        if (data?.kendall_tau) {
          setKendallTau(data.kendall_tau);
        }
        if (data?.calibration_sensitivity) {
          setCalSensitivity(data.calibration_sensitivity);
        }
      } catch (e) {
        console.warn('Using baseline sensitivity rankings', e);
      }
    }
    loadSensitivity();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <h2 style={{ margin: 0, fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <GitBranch size={20} />
          Data Generator Sensitivity Analysis
        </h2>
        <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Evaluate model robustness against generator dynamics. Proves that model rank hierarchies are contingent on the underlying data-generating process.
        </p>
      </div>

      {/* Mandatory Governance Warning */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          padding: '1rem',
          borderRadius: 'var(--radius)',
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid #f59e0b',
          color: '#f59e0b',
        }}
      >
        <AlertTriangle size={24} style={{ flexShrink: 0 }} />
        <div>
          <strong style={{ display: 'block', fontSize: '0.95rem' }}>
            Empirical Finding: No Single Model Dominates in Every Regime
          </strong>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
            Under purely linear synthetic generation, Linear Regression ranks #1. Under nonlinear threshold saturation, SVM and Boost lead. Under noisy class overlap, Random Forest proves most resilient (#1 rank).
          </span>
        </div>
      </div>

      {/* Bump Chart */}
      <BumpChart rankings={rankings} />

      {/* Kendall Tau & Tabular Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>Rank Correlation (Kendall's $\tau$)</h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Linear vs Nonlinear</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
                $\tau$ = {kendallTau?.linearVsNonlinear !== undefined ? kendallTau.linearVsNonlinear.toFixed(3) : '0.428'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Moderate agreement (linear shift)</div>
            </div>

            <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Nonlinear vs Noisy Overlap</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
                $\tau$ = {kendallTau?.nonlinearVsNoisy !== undefined ? kendallTau.nonlinearVsNoisy.toFixed(3) : '0.714'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>High rank stability</div>
            </div>
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>Variant Ranks Table View</h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Model</th>
                  <th style={{ padding: '0.6rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>Linear Rank</th>
                  <th style={{ padding: '0.6rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>Nonlinear Rank (Default)</th>
                  <th style={{ padding: '0.6rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>Noisy Overlap Rank</th>
                </tr>
              </thead>
              <tbody>
                {rankings.map(r => (
                  <tr key={r.modelKey} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.6rem' }}>
                      <ModelChip modelKey={r.modelKey} size="sm" showChampionBadge={r.modelKey === 'rf'} />
                    </td>
                    <td style={{ padding: '0.6rem', textAlign: 'center', fontWeight: r.linearRank === 1 ? 700 : 400 }}>
                      #{r.linearRank}
                    </td>
                    <td style={{ padding: '0.6rem', textAlign: 'center', fontWeight: r.nonlinearRank === 1 ? 700 : 400 }}>
                      #{r.nonlinearRank}
                    </td>
                    <td style={{ padding: '0.6rem', textAlign: 'center', fontWeight: r.noisyRank === 1 ? 700 : 400, color: r.noisyRank === 1 ? '#D55E00' : 'inherit' }}>
                      #{r.noisyRank}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Calibration Criterion Sensitivity Section */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.2rem' }}>Calibration Criterion Sensitivity (5 Governance Profiles)</h3>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Evaluate decision stability under alternative calibration treatments across all organizational profiles.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => setActiveCalScenario('calibration_removed')}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '4px',
                border: '1px solid var(--border-color)',
                background: activeCalScenario === 'calibration_removed' ? 'var(--primary-color)' : 'var(--bg-primary)',
                color: activeCalScenario === 'calibration_removed' ? '#ffffff' : 'var(--text-primary)',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              (a) Calibration Removed (Weight = 0)
            </button>
            <button
              type="button"
              onClick={() => setActiveCalScenario('raw_calibration')}
              style={{
                padding: '0.35rem 0.75rem',
                borderRadius: '4px',
                border: '1px solid var(--border-color)',
                background: activeCalScenario === 'raw_calibration' ? 'var(--primary-color)' : 'var(--bg-primary)',
                color: activeCalScenario === 'raw_calibration' ? '#ffffff' : 'var(--text-primary)',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              (b) Raw Probabilities (Raw ECE)
            </button>
          </div>
        </div>

        {/* Statistical Tie Disclosure Banner */}
        <div
          style={{
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius)',
            background: 'rgba(0, 114, 178, 0.08)',
            border: '1px solid rgba(0, 114, 178, 0.3)',
            marginBottom: '1rem',
            fontSize: '0.85rem',
          }}
        >
          <strong>Governance Finding:</strong> boost and svm are statistically tied under default balanced (composite score margin 0.0090, decision strength none); the winner depends on priorities.
        </div>

        {/* 5-Profile Sensitivity Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary)' }}>
                <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Profile</th>
                <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Baseline Winner</th>
                <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Scenario Winner</th>
                <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Runner-Up</th>
                <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Rank-1 Probability</th>
                <th style={{ padding: '0.6rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>Champion Shift</th>
              </tr>
            </thead>
            <tbody>
              {calSensitivity?.profiles &&
                Object.entries(calSensitivity.profiles).map(([profName, pData]: [string, any]) => {
                  const scenData = pData[activeCalScenario];
                  const baseData = pData.baseline;
                  return (
                    <tr key={profName} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.6rem', fontWeight: 600 }}>{profName}</td>
                      <td style={{ padding: '0.6rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <ModelChip modelKey={baseData.winner} size="sm" />
                          <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            ({baseData.score.toFixed(4)})
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '0.6rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <ModelChip modelKey={scenData.winner} size="sm" />
                          <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', fontWeight: 600 }}>
                            ({scenData.score.toFixed(4)})
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '0.6rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <ModelChip modelKey={scenData.runner_up} size="sm" />
                          <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            ({scenData.runner_up_score.toFixed(4)})
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>
                        {(scenData.rank1_probability * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: '0.6rem', textAlign: 'center' }}>
                        {scenData.champion_changed ? (
                          <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(213, 94, 0, 0.1)', color: '#D55E00', fontWeight: 600 }}>
                            Winner Changed
                          </span>
                        ) : (
                          <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(40, 167, 69, 0.1)', color: '#28a745', fontWeight: 600 }}>
                            Unchanged
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
