import { useState, useEffect } from 'react';
import { apiV2 } from '../../lib/api-client-v2';
import { MODEL_TOKENS } from '../../lib/tokens';
import { ModelChip } from '../ui/ModelChip';
import SceneFrame from './SceneFrame';
import { Compass, Info } from 'lucide-react';

const MODEL_KEYS = ['knn', 'rf', 'boost', 'svm', 'dt', 'logreg', 'linreg'];

interface PCAPoint {
  opaque_id: string;
  pc1: number;
  pc2: number;
  pc3: number;
  performance: 'Low' | 'Medium' | 'High';
}

interface NeighbourExplorerProps {
  tier?: 'high' | 'off';
  onTierChange?: (tier: 'high' | 'off') => void;
}

export function NeighbourExplorer({ tier = 'high' }: NeighbourExplorerProps) {
  const [selectedModel, setSelectedModel] = useState<string>('knn');
  const [points, setPoints] = useState<PCAPoint[]>([]);
  const [force2D, setForce2D] = useState(false);

  useEffect(() => {
    async function fetchPCA() {
      try {
        const data = await apiV2.getPCA();
        if (data?.background_points) {
          // Take first 300 points for smooth interactive rendering
          setPoints(data.background_points.slice(0, 300));
        }
      } catch (e) {
        console.warn('Using baseline PCA coordinates', e);
      }
    }
    fetchPCA();
  }, []);

  const isKNN = selectedModel === 'knn';
  const is2DMode = force2D || tier === 'off';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header & Model Switcher */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Compass size={18} />
              3D Feature Space & Neighbour Explorer
            </h3>
            <p style={{ margin: '0.2rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Inspect background training employees projected into the first 3 Principal Component axes (PC1, PC2, PC3).
            </p>
          </div>

          <button
            type="button"
            onClick={() => setForce2D(!force2D)}
            style={{
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
            {is2DMode ? '2D Projection Active' : 'Switch to 2D Fallback'}
          </button>
        </div>

        {/* Model Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Perspective:</span>
          {MODEL_KEYS.map(k => (
            <ModelChip
              key={k}
              modelKey={k}
              active={selectedModel === k}
              onClick={() => setSelectedModel(k)}
              size="sm"
              showChampionBadge={k === 'rf'}
            />
          ))}
        </div>
      </div>

      {/* Non-KNN Similar Cases Notice */}
      {!isKNN && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.85rem 1rem',
            borderRadius: 'var(--radius)',
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid #f59e0b',
            color: '#f59e0b',
            fontSize: '0.85rem',
          }}
        >
          <Info size={18} />
          <div>
            <strong>Similar-Cases Perspective:</strong>
            <span style={{ color: 'var(--text-primary)', marginLeft: '4px' }}>
              For {MODEL_TOKENS[selectedModel]?.name || selectedModel}, proximity in feature space represents descriptive historical analog cases, <em>not how this model decided</em>.
            </span>
          </div>
        </div>
      )}

      {/* 3D or 2D View */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', minHeight: '420px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {is2DMode ? (
          /* 2D Projection Fallback */
          <div data-testid="neighbour-2d-fallback" style={{ width: '100%', maxWidth: '440px', textAlign: 'center' }}>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}>
              2D Principal Component Projection (PC1 vs PC2)
            </div>
            <svg width="360" height="300" style={{ background: 'var(--bg-primary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', display: 'block', margin: '0 auto' }}>
              {points.map((pt) => {
                const cx = 180 + pt.pc1 * 40;
                const cy = 150 - pt.pc2 * 40;
                const color = pt.performance === 'High' ? '#10b981' : pt.performance === 'Medium' ? '#f59e0b' : '#ef4444';
                return (
                  <circle
                    key={pt.opaque_id}
                    cx={Math.max(10, Math.min(350, cx))}
                    cy={Math.max(10, Math.min(290, cy))}
                    r="3"
                    fill={color}
                    opacity={0.8}
                  />
                );
              })}
            </svg>
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Green: High | Amber: Medium | Red: Low | {points.length} Anonymized Background Points
            </div>
          </div>
        ) : (
          /* 3D SceneFrame View */
          <div style={{ width: '100%', height: '400px' }}>
            <SceneFrame
              tier={tier}
              fallback={
                <div data-testid="neighbour-fallback" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  3D View disabled or unavailable. 2D fallback engaged.
                </div>
              }
            >
              <ambientLight intensity={0.6} />
              <pointLight position={[5, 5, 5]} intensity={1.2} />

              <group rotation={[0.2, 0.4, 0]}>
                {points.slice(0, 80).map((pt) => {
                  const color = pt.performance === 'High' ? '#10b981' : pt.performance === 'Medium' ? '#f59e0b' : '#ef4444';
                  return (
                    <mesh key={pt.opaque_id} position={[pt.pc1 * 0.8, pt.pc2 * 0.8, pt.pc3 * 0.8]}>
                      <sphereGeometry args={[0.08, 8, 8]} />
                      <meshStandardMaterial color={color} />
                    </mesh>
                  );
                })}
              </group>
            </SceneFrame>
          </div>
        )}
      </div>
    </div>
  );
}
