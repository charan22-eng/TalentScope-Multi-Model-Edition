import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, NavLink, Navigate } from 'react-router-dom';
import PredictPage from './pages/Predict';
import BatchPage from './pages/Batch';
import DashboardPage from './pages/Dashboard';
import ModelLabPage from './pages/ModelLab';
import MethodologyPage from './pages/Methodology';
import DataExplorerPage from './pages/DataExplorer';
import ArenaPage from './pages/arena/ArenaPage';
import ThreePage from './pages/ThreePage';
import { Moon, Sun, Shield, Trophy, UserCheck } from 'lucide-react';
import { ClassChip } from './components/ui/ClassChip';
import { ensureAuthToken } from './lib/auth-bootstrap';
import './index.css';

const NAV_ITEMS = [
  { path: '/arena', label: 'Model Arena' },
  { path: '/predict', label: 'Predict' },
  { path: '/batch', label: 'Batch' },
  { path: '/dashboard', label: 'Dashboard' },
  { path: '/model-lab', label: 'Model Lab' },
  { path: '/data-explorer', label: 'Data Explorer' },
  { path: '/methodology', label: 'Methodology' },
  { path: '/3d', label: '3D Viewer' },
];

function AppShell({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('theme') as 'light' | 'dark') || 'dark';
  });
  const [userRole] = useState<string>(() => localStorage.getItem('user_role') || 'admin');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    void ensureAuthToken();
  }, []);

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-primary)' }}>
      {/* Sticky Glassmorphic Header */}
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          padding: '0.75rem 1.75rem',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: 'var(--glass-bg)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          {/* Brand Logo */}
          <Link
            to="/"
            style={{
              fontWeight: 800,
              fontSize: '1.25rem',
              color: 'var(--text-primary)',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--primary-action), #1d4ed8)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                boxShadow: 'var(--shadow-glow)',
              }}
            >
              <Shield size={18} />
            </div>
            <span style={{ fontFamily: 'Outfit, sans-serif', letterSpacing: '-0.02em' }}>TalentScope</span>
            <span
              className="badge-pill badge-champion"
              style={{ fontSize: '0.65rem', padding: '0.15rem 0.5rem', marginLeft: '0.2rem' }}
              title="Hist Gradient Boosting Champion Governed"
            >
              <Trophy size={11} />
              Boost
            </span>
          </Link>

          {/* Navigation Links */}
          <nav style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  padding: '0.45rem 0.85rem',
                  borderRadius: 'var(--radius-pill)',
                  textDecoration: 'none',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? '#ffffff' : 'var(--text-secondary)',
                  background: isActive ? 'var(--primary-action)' : 'transparent',
                  boxShadow: isActive ? 'var(--shadow-glow)' : 'none',
                  transition: 'all 0.15s ease',
                })}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* User Role, Theme, & Controls */}
        <div style={{ display: 'flex', gap: '0.85rem', alignItems: 'center' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.25rem 0.65rem',
              background: 'var(--bg-tertiary)',
              borderRadius: 'var(--radius-pill)',
              border: '1px solid var(--border-color)',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
            }}
          >
            <UserCheck size={13} color="var(--primary-color)" />
            <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{userRole}</span>
          </div>

          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius)',
              cursor: 'pointer',
              color: 'var(--text-primary)',
              width: '34px',
              height: '34px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease',
            }}
          >
            {theme === 'dark' ? <Sun size={17} color="#fbbf24" /> : <Moon size={17} color="#6366f1" />}
          </button>

        </div>
      </header>

      {/* Main Content Area */}
      <main className="container" style={{ flex: 1, padding: '1.75rem 1.25rem' }}>
        {children}
      </main>

      {/* Subtle Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-color)',
          padding: '1rem 1.5rem',
          textAlign: 'center',
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
          backgroundColor: 'var(--bg-secondary)',
        }}
      >
        TalentScope Multi-Model Performance Intelligence • Governed Champion: Hist Gradient Boosting (0.6665 Balanced MCDA)
      </footer>
    </div>
  );
}

function ComponentsPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <h2>Component Library</h2>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <ClassChip status="High" />
        <ClassChip status="Medium" />
        <ClassChip status="Low" />
        <ClassChip status="Unknown" />
      </div>
      <div>
        <label>
          Test Range Slider
          <input type="range" aria-label="Range Slider" />
        </label>
      </div>
      <div>
        <button onClick={() => alert('Dialog!')} aria-haspopup="dialog">Open Dialog</button>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<ArenaPage />} />
          <Route path="/arena/*" element={<ArenaPage />} />
          <Route path="/predict" element={<PredictPage />} />
          <Route path="/batch" element={<BatchPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/model-lab" element={<ModelLabPage />} />
          <Route path="/data-explorer" element={<DataExplorerPage />} />
          <Route path="/methodology" element={<MethodologyPage />} />
          <Route path="/3d" element={<ThreePage />} />
          <Route path="/components" element={<ComponentsPage />} />
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
