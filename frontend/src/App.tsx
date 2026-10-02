import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Home, Users, Settings, Activity, AlertTriangle, UserCheck, LogOut } from 'lucide-react';
import { Card } from './components/Card';
import { Button } from './components/Button';
import { api } from './api';
import type { PredictionRequest, PredictionResponse } from './api';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));

  const handleLogin = (newToken: string) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router>
      <div className="app-container">
        {/* Sidebar */}
        <nav className="sidebar">
          <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Activity color="var(--color-primary)" size={28} />
            <h2 style={{ fontSize: '1.25rem', color: 'var(--color-text)', margin: 0 }}>HR Insights</h2>
          </div>
          
          <Link to="/" style={{ textDecoration: 'none' }}>
            <div className="btn" style={{ width: '100%', justifyContent: 'flex-start', background: 'transparent', color: 'var(--color-text)' }}>
              <Home size={18} style={{ marginRight: '0.75rem' }} /> Dashboard
            </div>
          </Link>
          <Link to="/predict" style={{ textDecoration: 'none' }}>
            <div className="btn" style={{ width: '100%', justifyContent: 'flex-start', background: 'transparent', color: 'var(--color-text)' }}>
              <Users size={18} style={{ marginRight: '0.75rem' }} /> Predict Performance
            </div>
          </Link>
          <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div className="btn" style={{ width: '100%', justifyContent: 'flex-start', background: 'transparent', color: 'var(--color-text-muted)' }}>
              <Settings size={18} style={{ marginRight: '0.75rem' }} /> Settings
            </div>
            <button className="btn" onClick={handleLogout} style={{ width: '100%', justifyContent: 'flex-start', background: 'transparent', color: 'var(--color-danger)' }}>
              <LogOut size={18} style={{ marginRight: '0.75rem' }} /> Logout
            </button>
          </div>
        </nav>

        {/* Main Content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/predict" element={<Predict />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState('admin@hr.local');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.login(username, password);
      onLogin(res.access_token);
    } catch (err: any) {
      setError('Invalid credentials or Network Error (CORS)');
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--color-bg)' }} className="login-card-container">
      <div style={{ width: '400px' }}>
        <Card title="HR Insights Platform" className="login-card">
          <p style={{ marginBottom: '1.5rem', fontSize: '0.9rem' }}>Please sign in to access the prediction models.</p>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--color-text)' }}>
              <span>HR Email</span>
              <span style={{color: 'var(--color-text-muted)'}}>(admin@hr.local)</span>
            </label>
            <input type="email" value={username} onChange={e => setUsername(e.target.value)} className="input-field" required />
          </div>
          <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--color-text)' }}>
              <span>Password</span>
              <span style={{color: 'var(--color-text-muted)'}}>(admin123)</span>
            </label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="input-field" required />
          </div>
          {error && <div style={{ color: 'var(--color-danger)', fontSize: '0.875rem', padding: '0.5rem', backgroundColor: 'rgba(176, 74, 74, 0.1)', borderRadius: '0.25rem' }}>{error}</div>}
          <Button type="submit" style={{ marginTop: '0.5rem', width: '100%' }}>Sign In to Workspace</Button>
        </form>
      </Card>
      </div>
    </div>
  );
}

function Dashboard() {
  return (
    <div>
      <h1>Welcome to HR Insights</h1>
      <p style={{ marginBottom: '2rem' }}>AI-powered decision support for employee performance.</p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        <Card title="System Status">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--color-success)' }}></div>
            <span>Model v1.0 (KNN Tuned) is active and healthy.</span>
          </div>
        </Card>
        
        <Card title="Recent Activity">
          <p>System operational. Ready for predictions.</p>
        </Card>
      </div>
    </div>
  );
}

function Predict() {
  const [formData, setFormData] = useState<PredictionRequest>({
    attendance: 95,
    experience_years: 5,
    training_hours: 40,
    projects_completed: 5,
    weekly_hours: 40,
    prev_score: 3,
    department: 'Engineering',
    job_level: 'Mid'
  });
  
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.predict(formData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'An error occurred during prediction.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Predict Performance</h1>
      <p style={{ marginBottom: '2rem' }}>Enter employee metrics to get a performance band prediction.</p>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <Card title="Employee Profile">
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--color-text-muted)' }}>Attendance (%)</label>
                <input type="number" name="attendance" value={formData.attendance} onChange={handleChange} className="input-field" required min="0" max="100" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--color-text-muted)' }}>Experience (Years)</label>
                <input type="number" name="experience_years" value={formData.experience_years} onChange={handleChange} className="input-field" required min="0" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--color-text-muted)' }}>Training Hours</label>
                <input type="number" name="training_hours" value={formData.training_hours} onChange={handleChange} className="input-field" required min="0" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--color-text-muted)' }}>Projects Completed</label>
                <input type="number" name="projects_completed" value={formData.projects_completed} onChange={handleChange} className="input-field" required min="0" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--color-text-muted)' }}>Weekly Hours</label>
                <input type="number" name="weekly_hours" value={formData.weekly_hours} onChange={handleChange} className="input-field" required min="0" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--color-text-muted)' }}>Previous Score (1-5)</label>
                <input type="number" name="prev_score" value={formData.prev_score} onChange={handleChange} className="input-field" required min="1" max="5" step="0.1" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--color-text-muted)' }}>Department</label>
                <select name="department" value={formData.department} onChange={handleChange} className="input-field">
                  <option value="Engineering">Engineering</option>
                  <option value="Sales">Sales</option>
                  <option value="HR">HR</option>
                  <option value="Marketing">Marketing</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: 'var(--color-text-muted)' }}>Job Level</label>
                <select name="job_level" value={formData.job_level} onChange={handleChange} className="input-field">
                  <option value="Junior">Junior</option>
                  <option value="Mid">Mid</option>
                  <option value="Senior">Senior</option>
                  <option value="Lead">Lead</option>
                </select>
              </div>
            </div>
            {error && <div style={{ color: 'var(--color-danger)', fontSize: '0.875rem' }}>{error}</div>}
            <Button type="submit" disabled={loading} style={{ marginTop: '1rem' }}>
              {loading ? 'Analyzing...' : 'Run Prediction'}
            </Button>
          </form>
        </Card>

        <div>
          {result ? (
            <Card title="Analysis Result">
              <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: result.prediction === 'High' ? 'var(--color-success)' : result.prediction === 'Low' ? 'var(--color-danger)' : 'var(--color-warning)' }}>
                  {result.prediction}
                </div>
                <div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Confidence</div>
                  <div style={{ fontWeight: '500' }}>{(result.confidence * 100).toFixed(1)}%</div>
                </div>
              </div>

              {result.is_flagged && (
                <div style={{ padding: '0.75rem', backgroundColor: 'rgba(245, 158, 11, 0.1)', border: '1px solid var(--color-warning)', borderRadius: '0.5rem', color: 'var(--color-warning)', display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                  <AlertTriangle size={20} />
                  <span style={{ fontSize: '0.875rem' }}>Low confidence prediction. Human review required.</span>
                </div>
              )}

              <p style={{ fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>{result.summary}</p>
              
              <h4 style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>Nearest Neighbours</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {result.neighbours.map((nb, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', backgroundColor: 'var(--color-bg)', borderRadius: '0.25rem', fontSize: '0.875rem' }}>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                      <UserCheck size={14} color="var(--color-text-muted)" />
                      <span>{nb.employee_id}</span>
                      <span style={{ color: 'var(--color-text-muted)' }}>{nb.department}, {nb.job_level}</span>
                    </div>
                    <strong style={{ color: nb.class === 'High' ? 'var(--color-success)' : nb.class === 'Low' ? 'var(--color-danger)' : 'var(--color-warning)' }}>
                      {nb.class}
                    </strong>
                  </div>
                ))}
              </div>
              
              <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
                <Button variant="secondary" style={{ flex: 1, backgroundColor: 'var(--color-bg)', border: '1px solid var(--border-subtle)' }}>Override</Button>
                <Button style={{ flex: 1 }}>Accept</Button>
              </div>
            </Card>
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)', border: '2px dashed var(--border-subtle)', borderRadius: '0.75rem', padding: '2rem', textAlign: 'center' }}>
              Run a prediction to see the analysis and nearest neighbours.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
