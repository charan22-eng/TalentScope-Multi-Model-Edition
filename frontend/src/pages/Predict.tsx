import React, { useState } from 'react';
import { predict, type EmployeeFeatures, type PredictResponse } from '../lib/api-client';
import { ClassChip } from '../components/ui/ClassChip';

const DEPARTMENTS = ['Sales', 'Engineering', 'HR', 'Marketing', 'Finance'];
const LEVELS = ['Junior', 'Mid', 'Senior', 'Lead'];

export default function PredictPage() {
  const [form, setForm] = useState<EmployeeFeatures>({
    attendance: 90,
    experience_years: 5.0,
    training_hours: 40,
    projects_completed: 5,
    weekly_hours: 40,
    prev_score: 3,
    department: 'Engineering',
    job_level: 'Mid',
  });

  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [advisorMode, setAdvisorMode] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await predict(form);
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail?.[0]?.message || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof EmployeeFeatures, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div style={{ display: 'flex', gap: '2rem', padding: '2rem 0' }}>
      <div style={{ flex: 1 }}>
        <h2>Predict Performance</h2>
        <div style={{ marginBottom: '1rem' }}>
          <label>
            <input 
              type="checkbox" 
              checked={advisorMode} 
              onChange={e => setAdvisorMode(e.target.checked)} 
            />
            What-If Advisor Mode
          </label>
        </div>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Actionable Fields */}
          <label htmlFor="attendance">Attendance (%)</label>
          <input id="attendance" type="number" value={form.attendance} onChange={e => handleInputChange('attendance', parseInt(e.target.value))} required min={0} max={100} style={{ display: 'block', width: '100%', marginBottom: '1rem' }} />
          
          <label htmlFor="training">Training Hours</label>
          <input id="training" type="number" value={form.training_hours} onChange={e => handleInputChange('training_hours', parseInt(e.target.value))} required min={0} style={{ display: 'block', width: '100%', marginBottom: '1rem' }} />
          
          <label htmlFor="projects">Projects Completed</label>
          <input id="projects" type="number" value={form.projects_completed} onChange={e => handleInputChange('projects_completed', parseInt(e.target.value))} required min={0} style={{ display: 'block', width: '100%', marginBottom: '1rem' }} />
          
          <label htmlFor="weekly">Weekly Hours</label>
          <input id="weekly" type="number" value={form.weekly_hours} onChange={e => handleInputChange('weekly_hours', parseInt(e.target.value))} required min={0} max={168} style={{ display: 'block', width: '100%', marginBottom: '1rem' }} />

          {/* Locked Fields in Advisor Mode */}
          <label htmlFor="experience">Experience Years</label>
          <input id="experience" type="number" step="0.1" value={form.experience_years} onChange={e => handleInputChange('experience_years', parseFloat(e.target.value))} required min={0} disabled={advisorMode} style={{ display: 'block', width: '100%', marginBottom: '1rem' }} />
          
          <label htmlFor="prev_score">Previous Score (1-5)</label>
          <input id="prev_score" type="number" value={form.prev_score} onChange={e => handleInputChange('prev_score', parseInt(e.target.value))} required min={1} max={5} disabled={advisorMode} style={{ display: 'block', width: '100%', marginBottom: '1rem' }} />
          
          <label htmlFor="department">Department</label>
          <select id="department" value={form.department} onChange={e => handleInputChange('department', e.target.value)} disabled={advisorMode} style={{ display: 'block', width: '100%', marginBottom: '1rem' }}>
            {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
          
          <label htmlFor="job_level">Job Level</label>
          <select id="job_level" value={form.job_level} onChange={e => handleInputChange('job_level', e.target.value)} disabled={advisorMode} style={{ display: 'block', width: '100%', marginBottom: '1rem' }}>
            {LEVELS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>

          <button type="submit" disabled={loading} style={{ background: 'var(--primary-color)', color: 'white', padding: '0.75rem', borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer' }}>
            {loading ? 'Predicting...' : 'Predict'}
          </button>
        </form>
      </div>
      
      <div style={{ flex: 1, padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
        <h3>Results</h3>
        <div aria-live="polite">
          {error && <div style={{ color: 'var(--danger-color)' }}>Error: {error}</div>}
          
          {result && !error && (
            <div>
              <p>Prediction Set:</p>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                {result.prediction.map((p: string) => <ClassChip key={p} status={p as any} />)}
              </div>
              
              <p>Confidence: {(result.confidence * 100).toFixed(1)}%</p>
              <p>Stability Index: {result.stability_index.toFixed(1)} / 100</p>
              {result.stability_index < 70 && (
                <p style={{ color: 'var(--danger-color)', fontWeight: 'bold' }}>⚠️ Review Flag: High Uncertainty</p>
              )}
            </div>
          )}
          {!result && !error && !loading && <p>Submit the form to see predictions.</p>}
          {loading && <p>Loading results...</p>}
        </div>
      </div>
    </div>
  );
}
