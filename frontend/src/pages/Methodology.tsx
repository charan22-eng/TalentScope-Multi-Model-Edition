import { useState } from 'react';
import { MODEL_TOKENS } from '../lib/tokens';
import { ModelChip } from '../components/ui/ModelChip';
import { BookOpen, ShieldAlert, Award, FileText } from 'lucide-react';

const MODEL_DATA = {
  rf: {
    title: 'Random Forest (Ensemble) — Model Card',
    family: 'Ensemble of Bagged Decision Trees',
    champion: false,
    f1: '0.7787',
    acc: '77.6%',
    ece: '0.0157',
    latency: '60.2 ms',
    tier: 'Partial Native (Tree Path + Feature Importance)',
    details: 'Constructs an ensemble of de-correlated decision trees with randomized feature subsampling. Demonstrates high calibration fidelity, robustness to noise, and low extreme-error rate (0.21%).',
    limitations: 'Higher latency and memory footprint during inference compared to single decision tree.',
  },
  boost: {
    title: 'Histogram Gradient Boosting — Model Card',
    family: 'Ensemble Boosting',
    champion: true,
    f1: '0.8056',
    acc: '80.3%',
    ece: '0.0126 (Calibrated)',
    latency: '100.8 ms',
    tier: 'Partial Native (Gradient Tree Rules)',
    details: 'Bins continuous features into integer histograms for rapid gradient-boosted tree construction. Governed Arena Champion under ADR-014 temperature calibration Balanced MCDA profile (score 0.6665, p_rank1 0.555).',
    limitations: 'Sensitivity to extreme noise; requires multinomial temperature scaling for optimal probability calibration.',
  },
  svm: {
    title: 'Support Vector Machine (RBF) — Model Card',
    family: 'Kernel Machine',
    champion: false,
    f1: '0.8164 (Highest Raw Accuracy)',
    acc: '81.5%',
    ece: '0.0270',
    latency: '23.5 ms',
    tier: 'Model-Agnostic (Kernel Support Vectors)',
    details: 'Maximizes the margin between classes in an infinite-dimensional feature space using the Radial Basis Function (RBF) kernel. Achieved highest raw holdout accuracy, but lacks native human-interpretable feature rules.',
    limitations: 'Black-box dual representation; Platt calibration required for posterior probabilities.',
  },
  knn: {
    title: 'K-Nearest Neighbours — Model Card',
    family: 'Instance-Based Non-Parametric',
    champion: false,
    f1: '0.7543',
    acc: '75.2%',
    ece: '0.0246',
    latency: '16.9 ms',
    tier: 'Native (Neighbor Case Retrieval)',
    details: 'Classifies query candidates by uniform or distance-weighted votes among the k closest training employees in standardized Euclidean feature space. Native exemplar explanations through similar historical cases.',
    limitations: 'Inference scales linearly with training set size; sensitive to feature scaling.',
  },
  dt: {
    title: 'Decision Tree (CART) — Model Card',
    family: 'Hierarchical Rule Tree',
    champion: false,
    f1: '0.7094',
    acc: '70.8%',
    ece: '0.0342',
    latency: '16.3 ms (Ultra-fast)',
    tier: 'Native (Explicit Decision Rules)',
    details: 'Recursively partitions feature space using Gini impurity criteria. Generates intuitive if-then rules directly inspectable by HR professionals and compliance auditors.',
    limitations: 'Prone to high variance and step-function boundary artifacts.',
  },
  logreg: {
    title: 'Logistic Regression — Model Card',
    family: 'Generalized Linear Model',
    champion: false,
    f1: '0.7189',
    acc: '71.5%',
    ece: '0.1246',
    latency: '22.6 ms',
    tier: 'Native (Odds Ratios & Coefficients)',
    details: 'Multinomial logistic regression with L2 regularization. Provides direct log-odds interpretations per feature unit increase.',
    limitations: 'Cannot natively model complex nonlinear interactions without polynomial feature expansion.',
  },
  linreg: {
    title: 'Linear Regression (ScoreToBand) — Model Card',
    family: 'Continuous Regression Wrapper',
    champion: false,
    f1: '0.7032',
    acc: '70.1%',
    ece: '0.0213',
    latency: '13.2 ms (Lowest Latency)',
    tier: 'Native (Linear Feature Weights)',
    details: 'Trains on continuous performance score targets and maps predictions to ordered bands [0, 1, 2] via quantile threshold wrapper with out-of-fold Gaussian residual probabilities.',
    limitations: 'Rigid hyperplanar assumption; sensitive to non-Gaussian residual skew.',
  },
};

export default function MethodologyPage() {
  const [selectedTab, setSelectedTab] = useState<'comparison' | string>('comparison');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1rem 0' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <BookOpen size={24} color="var(--primary-color)" />
          Model Methodology & Architecture Cards
        </h1>
        <p style={{ margin: '0.35rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Comprehensive documentation, calibration protocols, fairness governance, and machine-generated model cards for the 7 arena models.
        </p>
      </div>

      {/* Mandatory Synthetic Caveat */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.75rem',
          padding: '1rem',
          borderRadius: 'var(--radius)',
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid var(--danger-color)',
        }}
      >
        <ShieldAlert size={20} color="var(--danger-color)" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.85rem' }}>
          <strong style={{ color: 'var(--danger-color)', display: 'block', marginBottom: '0.25rem' }}>
            CRITICAL GOVERNANCE NOTICE: Rankings Depend on Synthetic Generator Dynamics
          </strong>
          <span style={{ color: 'var(--text-primary)' }}>
            All metric hierarchies and model rankings reflect the frozen synthetic generator (Seed 42, 12,000 rows).
            Sensitivity testing across linear, nonlinear, and noisy-overlap variants demonstrates that <em>no single model dominates in every regime</em>.
            TalentScope provides decision support only and must not be used as an autonomous employment decision-maker.
          </span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        <button
          type="button"
          onClick={() => setSelectedTab('comparison')}
          style={{
            padding: '0.4rem 0.85rem',
            borderRadius: 'var(--radius)',
            border: `1px solid ${selectedTab === 'comparison' ? 'var(--primary-color)' : 'var(--border-color)'}`,
            background: selectedTab === 'comparison' ? 'var(--primary-color)' : 'var(--bg-secondary)',
            color: selectedTab === 'comparison' ? '#ffffff' : 'var(--text-primary)',
            fontWeight: 600,
            fontSize: '0.85rem',
            cursor: 'pointer',
          }}
        >
          <FileText size={14} style={{ display: 'inline', marginRight: '4px' }} />
          Comparison Card (All 7)
        </button>

        {Object.keys(MODEL_DATA).map((k) => (
          <ModelChip
            key={k}
            modelKey={k}
            active={selectedTab === k}
            onClick={() => setSelectedTab(k)}
            showChampionBadge={k === 'boost'}
            size="sm"
          />
        ))}
      </div>

      {/* Content Area */}
      {selectedTab === 'comparison' ? (
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.25rem', marginTop: 0 }}>Seven-Model Arena Comparison Card</h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Overview of the evaluation arena holding 7 architectures to identical fair comparison standards:
            frozen 60/10/10/20 stratified split, Platt calibration on disjoint cal-A, conformal sets on cal-B, and locked holdout test evaluation (G6).
          </p>

          <div style={{ margin: '1.5rem 0', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Model</th>
                  <th style={{ padding: '0.6rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Family</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Macro-F1</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Accuracy</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>ECE</th>
                  <th style={{ padding: '0.6rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Latency</th>
                  <th style={{ padding: '0.6rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>Explain Tier</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(MODEL_DATA).map(([k, d]) => (
                  <tr key={k} style={{ borderBottom: '1px solid var(--border-color)', background: d.champion ? 'rgba(213, 94, 0, 0.08)' : undefined }}>
                    <td style={{ padding: '0.6rem', fontWeight: 600 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ color: MODEL_TOKENS[k]?.color }}>{MODEL_TOKENS[k]?.marker}</span>
                        {MODEL_TOKENS[k]?.name}
                        {d.champion && <Award size={14} color="#D55E00" />}
                      </div>
                    </td>
                    <td style={{ padding: '0.6rem', color: 'var(--text-secondary)' }}>{d.family}</td>
                    <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{d.f1}</td>
                    <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{d.acc}</td>
                    <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{d.ece}</td>
                    <td style={{ padding: '0.6rem', textAlign: 'right', fontFamily: 'monospace' }}>{d.latency}</td>
                    <td style={{ padding: '0.6rem', textAlign: 'center', fontSize: '0.75rem' }}>{d.tier}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3 style={{ fontSize: '1.05rem', marginTop: '1.5rem' }}>Champion Selection Rule (ADR-009)</h3>
          <p style={{ fontSize: '0.85rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
            The Arena Champion is determined purely by algorithmic multi-criteria decision analysis (MCDA) under the Balanced priority profile.
            Random Forest (`rf`) achieves a composite score of 0.573 with a 64.2% rank-1 probability under 5,000 Dirichlet weight perturbations, earning a <strong>marginal</strong> decision strength rating.
          </p>
        </div>
      ) : (
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          {(() => {
            const card = MODEL_DATA[selectedTab as keyof typeof MODEL_DATA];
            if (!card) return null;
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ fontSize: '1.3rem', margin: 0 }}>{card.title}</h2>
                  <ModelChip modelKey={selectedTab} showChampionBadge={card.champion} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
                  <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Macro-F1</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{card.f1}</div>
                  </div>
                  <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Accuracy</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{card.acc}</div>
                  </div>
                  <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>ECE (Calibration)</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{card.ece}</div>
                  </div>
                  <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>p95 Latency</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{card.latency}</div>
                  </div>
                </div>

                <div>
                  <h3 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Architecture Description</h3>
                  <p style={{ fontSize: '0.85rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>{card.details}</p>
                </div>

                <div>
                  <h3 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>Known Limitations</h3>
                  <p style={{ fontSize: '0.85rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>{card.limitations}</p>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
