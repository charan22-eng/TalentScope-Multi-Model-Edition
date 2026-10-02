import { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import PredictPage from './pages/Predict';
import BatchPage from './pages/Batch';
import DashboardPage from './pages/Dashboard';
import ModelLabPage from './pages/ModelLab';
import MethodologyPage from './pages/Methodology';
import DataExplorerPage from './pages/DataExplorer';
import { Moon, Sun } from 'lucide-react';
import { ClassChip } from './components/ui/ClassChip';
import './index.css';

// Lazy loaded 3D scene frame
const SceneFrame = lazy(() => import('./components/three/SceneFrame'));

function AppShell({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('theme') as 'light' | 'dark') || 'dark';
  });
  const [showTour, setShowTour] = useState(true);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  // Command palette listener stub
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        alert('Command Palette opened!');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen">
      {showTour && (
        <aside aria-label="Onboarding Tour" style={{ background: 'var(--bg-secondary)', color: 'var(--text-primary)', padding: '1rem', textAlign: 'center', borderBottom: '1px solid var(--border-color)' }}>
          Welcome to the Onboarding Tour! <button onClick={() => setShowTour(false)} style={{ marginLeft: '1rem', padding: '0.25rem 0.5rem', background: 'var(--primary-color)', color: '#0f172a', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}>Skip Tour</button>
        </aside>
      )}
      <header style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <nav style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <Link to="/" style={{ fontWeight: 'bold', color: 'var(--text-primary)', textDecoration: 'none' }}>TalentScope</Link>
          <Link to="/predict" style={{ color: 'var(--text-primary)' }}>Predict</Link>
          <Link to="/batch" style={{ color: 'var(--text-primary)' }}>Batch</Link>
          <Link to="/dashboard" style={{ color: 'var(--text-primary)' }}>Dashboard</Link>
          <Link to="/model-lab" style={{ color: 'var(--text-primary)' }}>Model Lab</Link>
          <Link to="/data-explorer" style={{ color: 'var(--text-primary)' }}>Data Explorer</Link>
          <Link to="/methodology" style={{ color: 'var(--text-primary)' }}>Methodology</Link>
          <Link to="/3d" style={{ color: 'var(--text-primary)' }}>3D Viewer</Link>
        </nav>
        <button onClick={toggleTheme} aria-label="Toggle theme" style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-primary)' }}>
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </header>
      <main className="container">
        {children}
      </main>
    </div>
  );
}

function HomePage() {
  return (
    <div>
      <h1>Welcome to TalentScope</h1>
      <p>Data-driven employee performance intelligence.</p>
    </div>
  );
}

function ThreeViewerPage() {
  const [tier, setTier] = useState<'high' | 'off'>('high');

  return (
    <div>
      <h2>3D Galaxy Viewer</h2>
      <label style={{ display: 'block', marginBottom: '1rem' }}>
        Quality Tier:
        <select value={tier} onChange={(e) => setTier(e.target.value as 'high' | 'off')} style={{ marginLeft: '0.5rem' }}>
          <option value="high">High</option>
          <option value="off">Off (Fallback)</option>
        </select>
      </label>
      
      <Suspense fallback={<div>Loading 3D Engine...</div>}>
        <SceneFrame 
          tier={tier} 
          fallback={<div data-testid="scene-fallback" style={{ padding: '2rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', textAlign: 'center' }}>3D Visualization is currently disabled or unavailable.</div>}
        >
          {/* Simple rotating mesh for the test */}
          <mesh>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial color="hotpink" />
          </mesh>
          <ambientLight intensity={0.5} />
        </SceneFrame>
      </Suspense>
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
          <Route path="/" element={<HomePage />} />
          <Route path="/predict" element={<PredictPage />} />
          <Route path="/batch" element={<BatchPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/model-lab" element={<ModelLabPage />} />
          <Route path="/data-explorer" element={<DataExplorerPage />} />
          <Route path="/methodology" element={<MethodologyPage />} />
          <Route path="/3d" element={<ThreeViewerPage />} />
          <Route path="/components" element={<ComponentsPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
