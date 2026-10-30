import React, { useState } from 'react';
import { ArrowRight, Shield, Sparkles } from 'lucide-react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const DEMO_ACCOUNTS = [
  { role: 'Admin', email: 'admin@test.com', pass: 'admin' },
  { role: 'HR Manager', email: 'hr@test.com', pass: 'hr' },
  { role: 'Reviewer', email: 'reviewer@test.com', pass: 'reviewer' },
];

export function Login() {
  const [email, setEmail] = useState('admin@test.com');
  const [password, setPassword] = useState('admin');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email.trim());
      formData.append('password', password);
      const apiOrigin = import.meta.env.VITE_API_ORIGIN || 'http://localhost:8000';
      const response = await axios.post(`${apiOrigin}/login`, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user_role', response.data.role || 'viewer');
      localStorage.setItem('user_email', email.trim());
      navigate('/arena');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Login failed. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (acc: typeof DEMO_ACCOUNTS[0]) => {
    setEmail(acc.email);
    setPassword(acc.pass);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh', padding: '2rem 1rem' }}>
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '440px',
          padding: '2.25rem',
          boxShadow: 'var(--shadow-lg)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Glow accent */}
        <div
          style={{
            position: 'absolute',
            top: -40,
            right: -40,
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            background: 'var(--primary-glow)',
            filter: 'blur(30px)',
            pointerEvents: 'none',
          }}
        />

        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, var(--primary-action), #1d4ed8)',
              color: '#ffffff',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
              boxShadow: 'var(--shadow-glow)',
            }}
          >
            <Shield size={28} />
          </div>
          <h1 style={{ margin: '0 0 0.5rem', fontSize: '1.75rem', fontWeight: 800 }}>Sign in to TalentScope</h1>
          <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Enterprise multi-model governance & performance intelligence.
          </p>
        </div>

        {/* Quick Demo Persona Chips */}
        <div style={{ marginBottom: '1.5rem', padding: '0.85rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Sparkles size={12} color="var(--champion-gold)" />
            <span>ONE-CLICK DEMO ACCOUNTS:</span>
          </div>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {DEMO_ACCOUNTS.map(acc => (
              <button
                key={acc.email}
                type="button"
                onClick={() => fillCredentials(acc)}
                style={{
                  padding: '0.3rem 0.6rem',
                  borderRadius: 'var(--radius-pill)',
                  border: email === acc.email ? '1px solid var(--primary-color)' : '1px solid var(--border-color)',
                  background: email === acc.email ? 'var(--primary-glow)' : 'var(--bg-secondary)',
                  color: email === acc.email ? 'var(--primary-color)' : 'var(--text-primary)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {acc.role}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
          <div>
            <label htmlFor="email" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              style={{
                width: '100%',
                padding: '0.7rem 0.9rem',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius)',
                color: 'var(--text-primary)',
                fontSize: '0.9rem',
                transition: 'border-color 0.2s ease',
              }}
            />
          </div>

          <div>
            <label htmlFor="password" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              style={{
                width: '100%',
                padding: '0.7rem 0.9rem',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius)',
                color: 'var(--text-primary)',
                fontSize: '0.9rem',
                transition: 'border-color 0.2s ease',
              }}
            />
          </div>

          {error && (
            <div
              role="alert"
              style={{
                padding: '0.75rem 0.9rem',
                backgroundColor: 'var(--danger-glow)',
                border: '1px solid var(--danger-color)',
                color: 'var(--danger-color)',
                borderRadius: 'var(--radius)',
                fontSize: '0.825rem',
                fontWeight: 500,
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              width: '100%',
              padding: '0.85rem',
              backgroundColor: 'var(--primary-action)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius)',
              fontSize: '0.95rem',
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              boxShadow: 'var(--shadow-glow)',
              transition: 'all 0.2s ease',
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In to TalentScope'}
            <ArrowRight size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
