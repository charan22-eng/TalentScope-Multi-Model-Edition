import React, { useState } from 'react';
import { apiV2, type EmployeeFeatures, type PredictAllResponse, type ModelPrediction, type ExplainResponse } from '../lib/api-client-v2';
import { MODEL_TOKENS } from '../lib/tokens';
import { ModelChip } from '../components/ui/ModelChip';
import { ClassChip } from '../components/ui/ClassChip';
import { AlertTriangle, CheckCircle, Info, Sliders, Sparkles, User, Users } from 'lucide-react';

const DEPARTMENTS = ['Sales', 'Engineering', 'HR', 'Marketing', 'Finance'];
const LEVELS = ['Junior', 'Mid', 'Senior', 'Lead'];
const MODEL_KEYS = ['rf', 'boost', 'dt', 'knn', 'svm', 'logreg', 'linreg'];

export default function PredictPage() {
  const [selectedModel, setSelectedModel] = useState<string>('all');
  const [advisorMode, setAdvisorMode] = useState<boolean>(false);
  const [audience, setAudience] = useState<'hr' | 'ds'>('hr');

  const [form, setForm] = useState<EmployeeFeatures>({
    attendance: 92,
    experience_years: 5.0,
    training_hours: 45,
    projects_completed: 6,
    weekly_hours: 42,
    prev_score: 4,
    department: 'Engineering',
    job_level: 'Mid',
  });

  const [allResult, setAllResult] = useState<PredictAllResponse | null>(null);
  const [singleResult, setSingleResult] = useState<ModelPrediction | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (selectedModel === 'all') {
        const res = await apiV2.predictAll(form);
        setAllResult(res);
        setSingleResult(res.champion_prediction);
        // Also fetch explanation for champion
        const exp = await apiV2.explain(res.champion_prediction.model_key, form);
        setExplanation(exp);
      } else {
        const res = await apiV2.predictSingle(selectedModel, form);
        setSingleResult(res);
        setAllResult(null);
        const exp = await apiV2.explain(selectedModel, form);
        setExplanation(exp);
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(axiosErr.response?.data?.detail || (err instanceof Error ? err.message : String(err)));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof EmployeeFeatures, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1.5rem 0' }}>
      {/* Top Header & Model Selector */}
      <div style={{ background: 'var(--bg-secondary, #1e293b)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color, #334155)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.5rem' }}>TalentScope Prediction Suite</h1>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary, #94a3b8)', fontSize: '0.9rem' }}>
              Multi-model consensus and deep explainability across 7 validated machine learning architectures.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button
              type="button"
              onClick={() => setAdvisorMode(!advisorMode)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 0.85rem',
                borderRadius: 'var(--radius)',
                border: `1px solid ${advisorMode ? 'var(--primary-color)' : 'var(--border-color)'}`,
                background: advisorMode ? 'var(--primary-color)' : 'var(--bg-primary)',
                color: advisorMode ? '#ffffff' : 'var(--text-primary)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.85rem',
              }}
            >
              <Sliders size={16} />
              {advisorMode ? 'What-If Advisor: ON' : 'What-If Advisor: OFF'}
            </button>
          </div>
        </div>

        {/* Model Switcher Bar */}
        <div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
            SELECT MODEL MODE:
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <button
              type="button"
              onClick={() => setSelectedModel('all')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.35rem 0.85rem',
                borderRadius: '9999px',
                border: `2px solid ${selectedModel === 'all' ? 'var(--primary-color)' : 'var(--border-color)'}`,
                background: selectedModel === 'all' ? 'var(--primary-color)' : 'var(--bg-primary)',
                color: selectedModel === 'all' ? '#ffffff' : 'var(--text-primary)',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              <Users size={14} />
              All 7 Models (Consensus)
            </button>

            {MODEL_KEYS.map((k) => (
              <ModelChip
                key={k}
                modelKey={k}
                active={selectedModel === k}
                onClick={() => setSelectedModel(k)}
                showChampionBadge={true}
              />
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(400px, 1.4fr)', gap: '1.5rem' }}>
        {/* Input Form Column */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.2rem', marginTop: 0, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <User size={18} />
            Employee Candidate Profile
          </h2>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div>
              <label htmlFor="attendance" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.2rem' }}>
                Attendance Rate: {form.attendance}%
              </label>
              {advisorMode ? (
                <input
                  id="attendance"
                  type="range"
                  min={50}
                  max={100}
                  value={form.attendance}
                  onChange={e => handleInputChange('attendance', parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
              ) : (
                <input
                  id="attendance"
                  type="number"
                  min={0}
                  max={100}
                  value={form.attendance}
                  onChange={e => handleInputChange('attendance', parseInt(e.target.value))}
                  required
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                />
              )}
            </div>

            <div>
              <label htmlFor="training_hours" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.2rem' }}>
                Training Hours: {form.training_hours} hrs
              </label>
              {advisorMode ? (
                <input
                  id="training_hours"
                  type="range"
                  min={0}
                  max={120}
                  value={form.training_hours}
                  onChange={e => handleInputChange('training_hours', parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
              ) : (
                <input
                  id="training_hours"
                  type="number"
                  min={0}
                  value={form.training_hours}
                  onChange={e => handleInputChange('training_hours', parseInt(e.target.value))}
                  required
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                />
              )}
            </div>

            <div>
              <label htmlFor="projects_completed" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.2rem' }}>
                Projects Completed: {form.projects_completed}
              </label>
              {advisorMode ? (
                <input
                  id="projects_completed"
                  type="range"
                  min={0}
                  max={20}
                  value={form.projects_completed}
                  onChange={e => handleInputChange('projects_completed', parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
              ) : (
                <input
                  id="projects_completed"
                  type="number"
                  min={0}
                  value={form.projects_completed}
                  onChange={e => handleInputChange('projects_completed', parseInt(e.target.value))}
                  required
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                />
              )}
            </div>

            <div>
              <label htmlFor="weekly_hours" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.2rem' }}>
                Weekly Hours: {form.weekly_hours} hrs
              </label>
              {advisorMode ? (
                <input
                  id="weekly_hours"
                  type="range"
                  min={20}
                  max={70}
                  value={form.weekly_hours}
                  onChange={e => handleInputChange('weekly_hours', parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
              ) : (
                <input
                  id="weekly_hours"
                  type="number"
                  min={0}
                  max={168}
                  value={form.weekly_hours}
                  onChange={e => handleInputChange('weekly_hours', parseInt(e.target.value))}
                  required
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                />
              )}
            </div>

            {/* Non-actionable locked fields */}
            <div style={{ opacity: advisorMode ? 0.6 : 1 }}>
              <label htmlFor="experience_years" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.2rem' }}>
                Experience (Years) {advisorMode && '(Locked in Advisor)'}
              </label>
              <input
                id="experience_years"
                type="number"
                step="0.1"
                min={0}
                disabled={advisorMode}
                value={form.experience_years}
                onChange={e => handleInputChange('experience_years', parseFloat(e.target.value))}
                required
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              />
            </div>

            <div style={{ opacity: advisorMode ? 0.6 : 1 }}>
              <label htmlFor="prev_score" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.2rem' }}>
                Previous Review Score (1-5) {advisorMode && '(Locked)'}
              </label>
              <input
                id="prev_score"
                type="number"
                min={1}
                max={5}
                disabled={advisorMode}
                value={form.prev_score}
                onChange={e => handleInputChange('prev_score', parseInt(e.target.value))}
                required
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', opacity: advisorMode ? 0.6 : 1 }}>
              <div>
                <label htmlFor="department" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.2rem' }}>
                  Department
                </label>
                <select
                  id="department"
                  disabled={advisorMode}
                  value={form.department}
                  onChange={e => handleInputChange('department', e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                >
                  {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>

              <div>
                <label htmlFor="job_level" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.2rem' }}>
                  Job Level
                </label>
                <select
                  id="job_level"
                  disabled={advisorMode}
                  value={form.job_level}
                  onChange={e => handleInputChange('job_level', e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                >
                  {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '0.75rem',
                background: 'var(--primary-color, #2563eb)',
                color: '#ffffff',
                padding: '0.85rem',
                borderRadius: 'var(--radius)',
                border: 'none',
                fontWeight: 700,
                fontSize: '1rem',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Evaluating Models...' : selectedModel === 'all' ? 'Run All 7 Models' : `Predict with ${MODEL_TOKENS[selectedModel]?.name || selectedModel}`}
            </button>
          </form>
        </div>

        {/* Prediction Results Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {error && (
            <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger-color)', borderRadius: 'var(--radius)', color: 'var(--danger-color)' }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* All Models Panel View */}
          {allResult && (
            <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.25rem' }}>7-Model Consensus Arena</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Consensus:</span>
                  <ClassChip status={allResult.consensus_class} />
                </div>
              </div>

              {/* Agreement Meter */}
              <div style={{ marginBottom: '1.25rem', padding: '0.85rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem', fontWeight: 600 }}>
                  <span>Model Agreement Meter</span>
                  <span>{allResult.agreement_count} of {allResult.total_models} models agree ({(allResult.agreement_rate * 100).toFixed(0)}%)</span>
                </div>
                <div style={{ height: '8px', background: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${allResult.agreement_rate * 100}%`,
                      height: '100%',
                      background: allResult.agreement_rate >= 0.7 ? '#10b981' : allResult.agreement_rate >= 0.5 ? '#f59e0b' : '#ef4444',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>

              {/* Split Decision Warning */}
              {allResult.split_decision && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.85rem 1rem',
                    marginBottom: '1.25rem',
                    borderRadius: 'var(--radius)',
                    background: 'rgba(245, 158, 11, 0.12)',
                    border: '1px solid #f59e0b',
                    color: '#f59e0b',
                  }}
                >
                  <AlertTriangle size={20} />
                  <div>
                    <strong style={{ display: 'block', fontSize: '0.9rem' }}>Split-Decision Detected</strong>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                      Multiple models predict conflicting performance bands. Manual review or champion deference recommended.
                    </span>
                  </div>
                </div>
              )}

              {/* Model Prediction Grid */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {allResult.models_evaluated.map((key) => {
                  const pred = allResult.predictions[key];
                  const token = MODEL_TOKENS[key];
                  if (!pred) return null;

                  return (
                    <div
                      key={key}
                      style={{
                        padding: '0.75rem 1rem',
                        background: 'var(--bg-primary)',
                        borderRadius: 'var(--radius)',
                        border: pred.is_champion ? '2px solid #D55E00' : '1px solid var(--border-color)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.4rem',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ color: token?.color, fontWeight: 'bold' }}>{token?.marker}</span>
                          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{token?.name}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <ClassChip status={pred.top_class} />
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            ({(pred.probabilities[pred.top_class] * 100).toFixed(0)}%)
                          </span>
                        </div>
                      </div>

                      {/* Small probability bar */}
                      <div style={{ display: 'flex', height: '6px', borderRadius: '3px', overflow: 'hidden', background: 'var(--border-color)' }}>
                        <div style={{ width: `${pred.probabilities.Low * 100}%`, background: '#ef4444' }} title={`Low: ${(pred.probabilities.Low * 100).toFixed(1)}%`} />
                        <div style={{ width: `${pred.probabilities.Medium * 100}%`, background: '#f59e0b' }} title={`Medium: ${(pred.probabilities.Medium * 100).toFixed(1)}%`} />
                        <div style={{ width: `${pred.probabilities.High * 100}%`, background: '#10b981' }} title={`High: ${(pred.probabilities.High * 100).toFixed(1)}%`} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Single Model Result View */}
          {singleResult && !allResult && (
            <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.25rem' }}>
                  Prediction: {MODEL_TOKENS[singleResult.model_key]?.name || singleResult.model_key}
                </h3>
                <ClassChip status={singleResult.top_class} />
              </div>

              {/* Conformal Prediction Set */}
              <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.3rem' }}>
                  Conformal Prediction Set (α = 0.10, 90% Coverage Guarantee):
                </span>
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                  {singleResult.prediction_set.map(cls => (
                    <ClassChip key={cls} status={cls} />
                  ))}
                </div>
              </div>

              {/* Class Probability Distribution */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Probability Distribution:</span>
                {(['Low', 'Medium', 'High'] as const).map(cls => (
                  <div key={cls} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                    <span style={{ width: '60px' }}>{cls}:</span>
                    <div style={{ flex: 1, height: '8px', background: 'var(--bg-primary)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${singleResult.probabilities[cls] * 100}%`,
                          height: '100%',
                          background: cls === 'High' ? '#10b981' : cls === 'Medium' ? '#f59e0b' : '#ef4444',
                        }}
                      />
                    </div>
                    <span style={{ width: '45px', textAlign: 'right', fontFamily: 'monospace' }}>
                      {(singleResult.probabilities[cls] * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>

              {/* Indexes */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Stability Index</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{singleResult.stability_index.toFixed(1)} / 100</div>
                </div>
                <div style={{ padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Performance Index</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{singleResult.performance_index.toFixed(1)} / 100</div>
                </div>
              </div>
            </div>
          )}

          {/* Explanation Section following chosen model */}
          {explanation && (
            <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h4 style={{ margin: 0, fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Sparkles size={16} />
                  Model Explainability
                </h4>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 8px',
                      borderRadius: '9999px',
                      background: 'var(--primary-color)',
                      color: '#ffffff',
                      textTransform: 'uppercase',
                      fontWeight: 700,
                    }}
                  >
                    Tier: {explanation.explanation_type}
                  </span>
                  {/* Audience Toggle */}
                  <button
                    type="button"
                    onClick={() => setAudience(audience === 'hr' ? 'ds' : 'hr')}
                    style={{
                      fontSize: '0.75rem',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-primary)',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                    }}
                  >
                    Audience: {audience.toUpperCase()}
                  </button>
                </div>
              </div>

              {/* Natural language summary */}
              <p style={{ fontSize: '0.9rem', lineHeight: 1.5, color: 'var(--text-primary)', margin: '0 0 1rem 0' }}>
                {audience === 'hr' ? explanation.summary_hr : explanation.summary_ds}
              </p>

              {/* Counterfactual actionable recommendations */}
              {explanation.counterfactuals && explanation.counterfactuals.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem', color: 'var(--primary-color)' }}>
                    Actionable Improvement Pathways:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {explanation.counterfactuals.map((cf, idx) => (
                      <li key={idx} style={{ marginBottom: '0.25rem' }}>
                        Increase <strong>{cf.feature}</strong> from {cf.original_value} to {cf.proposed_value} (+{cf.delta}) to reach band <strong>{cf.target_class}</strong>.
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Similar cases view (labelled appropriately) */}
              {explanation.similar_cases && explanation.similar_cases.length > 0 && (
                <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                    <Info size={14} />
                    <span>Similar Historical Cases</span>
                    {explanation.model_key !== 'knn' && (
                      <span style={{ fontSize: '0.7rem', color: '#f59e0b', fontStyle: 'italic' }}>
                        (Note: not how this model decided)
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {explanation.similar_cases.map(c => (
                      <div key={c.id} style={{ padding: '0.4rem 0.6rem', background: 'var(--bg-primary)', borderRadius: '4px', fontSize: '0.75rem' }}>
                        Case #{c.id} (dist: {c.distance.toFixed(2)}) → <ClassChip status={c.predicted_band as 'High'|'Medium'|'Low'|'Unknown'} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!allResult && !singleResult && !loading && (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
              <CheckCircle size={36} style={{ margin: '0 auto 1rem auto', opacity: 0.5 }} />
              <p style={{ margin: 0 }}>Configure candidate features and click predict to evaluate models.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
