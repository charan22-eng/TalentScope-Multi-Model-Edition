import { useState, useEffect, useMemo } from 'react';
import { apiV2 } from '../../lib/api-client-v2';
import SceneFrame from './SceneFrame';
import { Layers, Eye } from 'lucide-react';

const MODEL_KEYS = ['rf', 'boost', 'svm', 'knn', 'dt', 'logreg', 'linreg'];

interface SurfaceData {
  feature_x: string;
  feature_y: string;
  grid_size: number;
  x_range: [number, number];
  y_range: [number, number];
  prob_high_surface: number[][];
}

interface DecisionLandscapeProps {
  tier?: 'high' | 'off';
  onTierChange?: (tier: 'high' | 'off') => void;
}

export function DecisionLandscape({ tier = 'high', onTierChange }: DecisionLandscapeProps) {
  const [modelA, setModelA] = useState<string>('rf');
  const [modelB, setModelB] = useState<string>('boost');
  const [mode, setMode] = useState<'single' | 'overlay' | 'difference'>('single');
  const [surfaceA, setSurfaceA] = useState<SurfaceData | null>(null);
  const [surfaceB, setSurfaceB] = useState<SurfaceData | null>(null);
  const [force2D, setForce2D] = useState(false);

  useEffect(() => {
    async function loadSurfaces() {
      try {
        const [resA, resB] = await Promise.all([
          apiV2.getSurface(modelA),
          apiV2.getSurface(modelB),
        ]);
        setSurfaceA(resA);
        setSurfaceB(resB);
      } catch (e) {
        console.error('Failed to load decision surfaces', e);
      }
    }
    loadSurfaces();
  }, [modelA, modelB]);

  // Compute 2D grid matrix depending on mode
  const displayMatrix = useMemo(() => {
    if (!surfaceA?.prob_high_surface) return [];
    const matA = surfaceA.prob_high_surface;
    const matB = surfaceB?.prob_high_surface || matA;
    const size = matA.length;

    const res: number[][] = [];
    for (let r = 0; r < size; r++) {
      const row: number[] = [];
      for (let c = 0; c < size; c++) {
        if (mode === 'difference') {
          // Diverging delta P_A - P_B
          row.push((matA[r]?.[c] ?? 0) - (matB[r]?.[c] ?? 0));
        } else {
          row.push(matA[r]?.[c] ?? 0);
        }
      }
      res.push(row);
    }
    return res;
  }, [surfaceA, surfaceB, mode]);

  // Color generator for 2D Heatmap & 3D points
  const getColor = (val: number) => {
    if (mode === 'difference') {
      // Diverging scale: -0.5 (blue) -> 0.0 (gray/dark) -> +0.5 (orange/red)
      if (val > 0) {
        const intensity = Math.min(val * 2.5, 1.0);
        return `rgba(213, 94, 0, ${0.2 + intensity * 0.8})`;
      } else {
        const intensity = Math.min(Math.abs(val) * 2.5, 1.0);
        return `rgba(86, 180, 233, ${0.2 + intensity * 0.8})`;
      }
    } else {
      // Sequential probability scale 0 -> 1: red -> amber -> teal
      if (val > 0.6) return `rgba(5, 150, 105, ${0.3 + val * 0.7})`;
      if (val > 0.35) return `rgba(217, 119, 6, ${0.3 + val * 0.7})`;
      return `rgba(220, 38, 38, ${0.3 + (1 - val) * 0.7})`;
    }
  };

  const is2DMode = force2D || tier === 'off';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Controls Bar */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={18} />
              Decision Boundary Landscape (P(High))
            </h3>
            <p style={{ margin: '0.2rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Feature slice: <strong>attendance</strong> vs <strong>projects_completed</strong>.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            {/* View Mode Toggle */}
            <button
              type="button"
              onClick={() => setForce2D(!force2D)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '0.4rem 0.8rem',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border-color)',
                background: is2DMode ? 'var(--primary-color)' : 'var(--bg-primary)',
                color: is2DMode ? '#ffffff' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              <Eye size={14} />
              {is2DMode ? '2D Heatmap Active' : 'Switch to 2D Fallback'}
            </button>

            {onTierChange && (
              <select
                value={tier}
                onChange={e => onTierChange(e.target.value as 'high' | 'off')}
                style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.8rem' }}
              >
                <option value="high">3D Tier: High</option>
                <option value="off">3D Tier: Off (A11y Fallback)</option>
              </select>
            )}
          </div>
        </div>

        {/* Model & Comparison Mode Selectors */}
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginRight: '0.5rem' }}>Mode:</span>
            {(['single', 'difference'] as const).map(m => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                style={{
                  padding: '0.3rem 0.6rem',
                  marginRight: '0.3rem',
                  borderRadius: '4px',
                  border: `1px solid ${mode === m ? 'var(--primary-color)' : 'var(--border-color)'}`,
                  background: mode === m ? 'var(--primary-color)' : 'var(--bg-primary)',
                  color: mode === m ? '#ffffff' : 'var(--text-primary)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  fontWeight: mode === m ? 700 : 400,
                }}
              >
                {m === 'single' ? 'Single Model (P)' : 'Difference Surface (P_A − P_B)'}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Model A:</span>
            <select
              value={modelA}
              onChange={e => setModelA(e.target.value)}
              style={{ padding: '0.3rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.8rem' }}
            >
              {MODEL_KEYS.map(k => <option key={k} value={k}>{k.toUpperCase()}</option>)}
            </select>
          </div>

          {mode === 'difference' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Model B:</span>
              <select
                value={modelB}
                onChange={e => setModelB(e.target.value)}
                style={{ padding: '0.3rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.8rem' }}
              >
                {MODEL_KEYS.map(k => <option key={k} value={k}>{k.toUpperCase()}</option>)}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Surface View (3D or 2D Heatmap Fallback) */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', minHeight: '420px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        {is2DMode ? (
          /* 2D Heatmap Fallback */
          <div data-testid="surface-2d-fallback" style={{ width: '100%', maxWidth: '480px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>
              2D High-Resolution Probability Grid (40 × 40)
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: `repeat(${displayMatrix.length || 40}, 1fr)`,
                width: '360px',
                height: '360px',
                border: '2px solid var(--border-color)',
                borderRadius: '4px',
                overflow: 'hidden',
              }}
            >
              {displayMatrix.map((row, rIdx) =>
                row.map((val, cIdx) => (
                  <div
                    key={`${rIdx}-${cIdx}`}
                    style={{
                      background: getColor(val),
                      width: '100%',
                      height: '100%',
                    }}
                    title={`Coords (${rIdx}, ${cIdx}) Value: ${val.toFixed(3)}`}
                  />
                ))
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', width: '360px', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <span>Attendance: 60%</span>
              <span>100%</span>
            </div>

            <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              {mode === 'difference' ? (
                <span>Legend: Blue (Favors {modelB.toUpperCase()}) ← 0.0 → Orange (Favors {modelA.toUpperCase()})</span>
              ) : (
                <span>Legend: Red (Low P) → Amber (Mid P) → Green (High P)</span>
              )}
            </div>
          </div>
        ) : (
          /* 3D SceneFrame Canvas View */
          <div style={{ width: '100%', height: '400px', position: 'relative' }}>
            <SceneFrame
              tier={tier}
              fallback={
                <div data-testid="surface-fallback" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  WebGL unavailable or prefers-reduced-motion active. 2D fallback engaged.
                </div>
              }
            >
              <ambientLight intensity={0.7} />
              <pointLight position={[10, 10, 10]} intensity={1.0} />

              {/* Parametric surface mesh representing the decision landscape */}
              <mesh rotation={[-Math.PI / 3, 0, 0]}>
                <planeGeometry args={[5, 5, 30, 30]} />
                <meshStandardMaterial
                  color={mode === 'difference' ? '#D55E00' : '#009E73'}
                  wireframe={true}
                  roughness={0.4}
                />
              </mesh>
            </SceneFrame>
          </div>
        )}
      </div>
    </div>
  );
}
