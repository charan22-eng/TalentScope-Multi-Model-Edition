import { useState, useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from '@react-three/drei';
import { apiV2 } from '../../lib/api-client-v2';
import SceneFrame from './SceneFrame';
import { Layers, Eye, RotateCcw, Box, Info } from 'lucide-react';
import { ModelChip } from '../ui/ModelChip';

const MODEL_KEYS = ['rf', 'boost', 'svm', 'knn', 'dt', 'logreg', 'linreg'];

const MODEL_DESCRIPTIONS: Record<string, string> = {
  boost: 'Champion (ADR-009/014): Smooth non-linear gradient boosting contour with temperature calibration.',
  rf: 'Bagged ensemble: Multi-tree smoothed terrain with reduced variance.',
  svm: 'Kernel Machine: RBF dual representation showing curved margin ridge.',
  dt: 'Hierarchical CART: Distinct rectilinear step-function plateaus.',
  knn: 'Instance-Based: Localized distance-weighted probability ripples.',
  logreg: 'Generalized Linear: Monotonic smooth sigmoid plane.',
  linreg: 'Continuous Wrapper: Planar score slope with quantile threshold cutoffs.',
};

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

/**
 * 3D Dynamic Heightfield Terrain Mesh
 * Renders vertex-displaced probability landscape from the 40x40 matrix.
 */
function LandscapeMesh({
  matrix,
  mode,
  wireframe,
}: {
  matrix: number[][];
  mode: 'single' | 'difference';
  wireframe: boolean;
}) {
  const meshRef = useRef<THREE.Mesh>(null);

  const geometry = useMemo(() => {
    const size = matrix.length || 40;
    // PlaneGeometry with width 5, height 5, segments size-1
    const geom = new THREE.PlaneGeometry(5, 5, size - 1, size - 1);
    const pos = geom.attributes.position;
    const colors = new Float32Array(pos.count * 3);

    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const val = matrix[r]?.[c] ?? 0;
        const idx = r * size + c;

        // Displace Z height based on probability or difference
        const height = mode === 'difference' ? val * 1.8 : val * 1.5;
        pos.setZ(idx, height);

        // Vertex color interpolation
        if (mode === 'difference') {
          // Bipolar palette: Orange (A > B) <-> Slate (A ≈ B) <-> Blue (B > A)
          if (val > 0) {
            const intensity = Math.min(val * 2.2, 1.0);
            colors[idx * 3] = 0.85 + 0.15 * intensity;
            colors[idx * 3 + 1] = 0.45 * (1 - intensity);
            colors[idx * 3 + 2] = 0.05;
          } else {
            const intensity = Math.min(Math.abs(val) * 2.2, 1.0);
            colors[idx * 3] = 0.15 * (1 - intensity);
            colors[idx * 3 + 1] = 0.45 + 0.3 * intensity;
            colors[idx * 3 + 2] = 0.95;
          }
        } else {
          // Sequential: Crimson (Low P) -> Amber (Mid P) -> Emerald (High P)
          if (val >= 0.6) {
            const t = Math.min((val - 0.6) / 0.4, 1.0);
            colors[idx * 3] = 0.06 * (1 - t) + 0.12 * t;
            colors[idx * 3 + 1] = 0.72 + 0.2 * t;
            colors[idx * 3 + 2] = 0.51 + 0.2 * t;
          } else if (val >= 0.35) {
            const t = (val - 0.35) / 0.25;
            colors[idx * 3] = 0.96;
            colors[idx * 3 + 1] = 0.62 + 0.12 * t;
            colors[idx * 3 + 2] = 0.07;
          } else {
            const t = Math.max(0, val / 0.35);
            colors[idx * 3] = 0.92;
            colors[idx * 3 + 1] = 0.2 + 0.18 * t;
            colors[idx * 3 + 2] = 0.2;
          }
        }
      }
    }

    geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    pos.needsUpdate = true;
    geom.computeVertexNormals();
    return geom;
  }, [matrix, mode]);

  return (
    <group rotation={[-Math.PI / 3, 0, 0]}>
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial
          vertexColors
          wireframe={wireframe}
          roughness={0.35}
          metalness={0.12}
          side={THREE.DoubleSide}
        />
      </mesh>
      {/* Base Spatial Reference Grid */}
      <gridHelper args={[5.6, 14, '#475569', '#1e293b']} position={[0, 0, -0.05]} rotation={[Math.PI / 2, 0, 0]} />
    </group>
  );
}

export function DecisionLandscape({ tier = 'high', onTierChange }: DecisionLandscapeProps) {
  const [modelA, setModelA] = useState<string>('boost');
  const [modelB, setModelB] = useState<string>('svm');
  const [mode, setMode] = useState<'single' | 'difference'>('single');
  const [surfaceA, setSurfaceA] = useState<SurfaceData | null>(null);
  const [surfaceB, setSurfaceB] = useState<SurfaceData | null>(null);
  const [force2D, setForce2D] = useState(false);
  const [wireframe, setWireframe] = useState(false);
  const [hoverCoord, setHoverCoord] = useState<{ x: number; y: number; val: number } | null>(null);

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

  // Color generator for 2D Heatmap
  const getColor = (val: number) => {
    if (mode === 'difference') {
      if (val > 0) {
        const intensity = Math.min(val * 2.2, 1.0);
        return `rgba(217, 119, 6, ${0.25 + intensity * 0.75})`;
      } else {
        const intensity = Math.min(Math.abs(val) * 2.2, 1.0);
        return `rgba(37, 99, 235, ${0.25 + intensity * 0.75})`;
      }
    } else {
      if (val >= 0.6) return `rgba(16, 185, 129, ${0.3 + val * 0.7})`;
      if (val >= 0.35) return `rgba(245, 158, 11, ${0.3 + val * 0.7})`;
      return `rgba(239, 68, 68, ${0.3 + (1 - val) * 0.7})`;
    }
  };

  const is2DMode = force2D || tier === 'off';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Controls Bar */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.3rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Layers size={20} color="var(--primary-color)" />
              3D Decision Boundary Topography (P(High))
            </h3>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              Feature slice: <strong>attendance</strong> (X-axis) vs <strong>projects_completed</strong> (Y-axis) with predicted probability elevation (Z-axis).
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => setWireframe(!wireframe)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border-color)',
                background: wireframe ? 'var(--primary-color)' : 'var(--bg-secondary)',
                color: wireframe ? '#ffffff' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              <Box size={14} />
              {wireframe ? 'Wireframe: ON' : 'Wireframe: OFF'}
            </button>

            <button
              type="button"
              onClick={() => setForce2D(!force2D)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border-color)',
                background: is2DMode ? 'var(--primary-color)' : 'var(--bg-secondary)',
                color: is2DMode ? '#ffffff' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              <Eye size={14} />
              {is2DMode ? '2D Projection Active' : 'Switch to 2D Fallback'}
            </button>

            {onTierChange && (
              <select
                value={tier}
                onChange={e => onTierChange(e.target.value as 'high' | 'off')}
                style={{ padding: '0.45rem 0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.8rem', fontWeight: 500 }}
              >
                <option value="high">3D Tier: High (WebGL)</option>
                <option value="off">3D Tier: Off (A11y Fallback)</option>
              </select>
            )}
          </div>
        </div>

        {/* Mode & Model Selectors */}
        <div style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginRight: '0.5rem', fontWeight: 600 }}>Visual Mode:</span>
            {(['single', 'difference'] as const).map(m => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                style={{
                  padding: '0.35rem 0.75rem',
                  marginRight: '0.4rem',
                  borderRadius: 'var(--radius-pill)',
                  border: `1px solid ${mode === m ? 'var(--primary-color)' : 'var(--border-color)'}`,
                  background: mode === m ? 'var(--primary-color)' : 'var(--bg-secondary)',
                  color: mode === m ? '#ffffff' : 'var(--text-primary)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  fontWeight: mode === m ? 700 : 500,
                  transition: 'all 0.15s ease',
                }}
              >
                {m === 'single' ? 'Single Architecture Landscape' : 'Differential Surface (Model A − Model B)'}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Model A:</span>
            {MODEL_KEYS.map(k => (
              <ModelChip
                key={k}
                modelKey={k}
                active={modelA === k}
                onClick={() => setModelA(k)}
                size="sm"
                showChampionBadge={k === 'boost'}
              />
            ))}
          </div>

          {mode === 'difference' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', borderLeft: '1px solid var(--border-color)', paddingLeft: '1rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Model B:</span>
              {MODEL_KEYS.map(k => (
                <ModelChip
                  key={k}
                  modelKey={k}
                  active={modelB === k}
                  onClick={() => setModelB(k)}
                  size="sm"
                  showChampionBadge={k === 'boost'}
                />
              ))}
            </div>
          )}
        </div>

        {/* Architecture Note */}
        <div style={{ marginTop: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
          <Info size={15} color="var(--primary-color)" />
          <span>{MODEL_DESCRIPTIONS[modelA] || modelA}</span>
        </div>
      </div>

      {/* Surface View (3D Canvas or 2D Heatmap Fallback) */}
      <div className="glass-panel" style={{ padding: '1.5rem', minHeight: '440px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        {is2DMode ? (
          /* 2D Heatmap Fallback */
          <div data-testid="surface-2d-fallback" style={{ width: '100%', maxWidth: '520px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ marginBottom: '0.75rem', fontSize: '0.9rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>2D High-Resolution Probability Grid (40 × 40)</span>
              {hoverCoord && (
                <span className="badge-pill badge-neutral" style={{ fontSize: '0.75rem' }}>
                  P(High): {(hoverCoord.val).toFixed(3)}
                </span>
              )}
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: `repeat(${displayMatrix.length || 40}, 1fr)`,
                width: '380px',
                height: '380px',
                border: '2px solid var(--border-color)',
                borderRadius: 'var(--radius)',
                overflow: 'hidden',
                boxShadow: 'var(--shadow-md)',
              }}
            >
              {displayMatrix.map((row, rIdx) =>
                row.map((val, cIdx) => (
                  <div
                    key={`${rIdx}-${cIdx}`}
                    onMouseEnter={() => setHoverCoord({ x: cIdx, y: rIdx, val })}
                    onMouseLeave={() => setHoverCoord(null)}
                    style={{
                      background: getColor(val),
                      width: '100%',
                      height: '100%',
                      transition: 'background 0.15s ease',
                    }}
                    title={`Coords (${rIdx}, ${cIdx}) Value: ${val.toFixed(3)}`}
                  />
                ))
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', width: '380px', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              <span>Attendance: 69%</span>
              <span>Projects Completed: 0 → 20</span>
              <span>100%</span>
            </div>

            <div style={{ marginTop: '0.85rem', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', gap: '1rem', alignItems: 'center' }}>
              {mode === 'difference' ? (
                <span>Legend: Blue (Favors {modelB.toUpperCase()}) ← 0.0 → Orange (Favors {modelA.toUpperCase()})</span>
              ) : (
                <span>Legend: Crimson (Low P) → Amber (Mid P) → Emerald (High P)</span>
              )}
            </div>
          </div>
        ) : (
          /* 3D SceneFrame Canvas View with Interactive OrbitControls & Dynamic Mesh */
          <div style={{ width: '100%', height: '460px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: 12, left: 16, zIndex: 10, background: 'rgba(15, 23, 42, 0.75)', backdropFilter: 'blur(8px)', padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-pill)', border: '1px solid var(--border-color)', fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <RotateCcw size={13} />
              <span>Left-click drag to rotate • Right-click drag to pan • Scroll to zoom</span>
            </div>

            <SceneFrame
              tier={tier}
              fallback={
                <div data-testid="surface-fallback" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  WebGL unavailable or prefers-reduced-motion active. 2D fallback engaged.
                </div>
              }
            >
              <ambientLight intensity={0.8} />
              <pointLight position={[10, 15, 10]} intensity={1.4} />
              <pointLight position={[-10, -10, -10]} intensity={0.4} />

              <LandscapeMesh matrix={displayMatrix} mode={mode} wireframe={wireframe} />

              <OrbitControls
                enableDamping
                dampingFactor={0.06}
                maxPolarAngle={Math.PI / 2 + 0.25}
                minDistance={3}
                maxDistance={12}
              />
            </SceneFrame>
          </div>
        )}
      </div>
    </div>
  );
}
