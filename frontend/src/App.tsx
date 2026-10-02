import { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Moon, Sun } from 'lucide-react';
import { ClassChip } from './components/ui/ClassChip';
import './index.css';

// Lazy loaded 3D scene frame
const SceneFrame = lazy(() => import('./components/three/SceneFrame'));

function AppShell({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('theme') as 'light' | 'dark') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  return (
    <div className="min-h-screen">
      <header style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <nav style={{ display: 'flex', gap: '1rem' }}>
          <Link to="/" style={{ fontWeight: 'bold', color: 'var(--text-primary)', textDecoration: 'none' }}>TalentScope</Link>
          <Link to="/3d" style={{ color: 'var(--text-primary)' }}>3D Viewer</Link>
          <Link to="/components" style={{ color: 'var(--text-primary)' }}>Components</Link>
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
          <Route path="/3d" element={<ThreeViewerPage />} />
          <Route path="/components" element={<ComponentsPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
