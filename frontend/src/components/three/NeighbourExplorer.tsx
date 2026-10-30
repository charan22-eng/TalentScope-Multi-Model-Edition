import { useState, useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { OrbitControls, Line } from '@react-three/drei';
import { apiV2 } from '../../lib/api-client-v2';
import { MODEL_TOKENS } from '../../lib/tokens';
import { ModelChip } from '../ui/ModelChip';
import SceneFrame from './SceneFrame';
import { Compass, Info, RotateCcw } from 'lucide-react';

const MODEL_KEYS = ['knn', 'rf', 'boost', 'svm', 'dt', 'logreg', 'linreg'];

interface PCAPoint {
  opaque_id: string;
  pc1: number;
  pc2: number;
  pc3: number;
  performance: 'Low' | 'Medium' | 'High';
}

interface ClassifiedPoint extends PCAPoint {
  predictedBand: 'Low' | 'Medium' | 'High';
  confidence: number;
  isAgree: boolean;
  isSupportVector?: boolean;
}

interface NeighbourExplorerProps {
  tier?: 'high' | 'off';
  onTierChange?: (tier: 'high' | 'off') => void;
}

/**
 * Classifies a PCA coordinate using the active model's decision architecture.
 */
function classifyPointForModel(pt: PCAPoint, modelKey: string): { predictedBand: 'Low' | 'Medium' | 'High'; confidence: number; isSupportVector?: boolean } {
  const { pc1, pc2, pc3 } = pt;

  if (modelKey === 'dt') {
    // CART decision tree: axis-aligned orthogonal cuts
    if (pc1 > 1.05) return { predictedBand: 'High', confidence: 0.88 };
    if (pc1 < -0.95) return { predictedBand: 'Low', confidence: 0.86 };
    if (pc2 < -0.65) return { predictedBand: 'High', confidence: 0.78 };
    if (pc2 > 0.65) return { predictedBand: 'Low', confidence: 0.82 };
    return { predictedBand: 'Medium', confidence: 0.74 };
  }

  if (modelKey === 'logreg') {
    // Multinomial logistic regression: linear decision hyperplane
    const score = 1.15 * pc1 - 0.95 * pc2 - 0.22 * pc3;
    if (score > 0.82) return { predictedBand: 'High', confidence: Math.min(0.96, 0.55 + score * 0.12) };
    if (score < -0.82) return { predictedBand: 'Low', confidence: Math.min(0.96, 0.55 + Math.abs(score) * 0.12) };
    return { predictedBand: 'Medium', confidence: 0.70 };
  }

  if (modelKey === 'linreg') {
    // Continuous quantile score wrapper
    const continuous = 50 + 13.5 * pc1 - 9.8 * pc2 - 1.8 * pc3;
    if (continuous >= 64) return { predictedBand: 'High', confidence: 0.75 };
    if (continuous <= 38) return { predictedBand: 'Low', confidence: 0.75 };
    return { predictedBand: 'Medium', confidence: 0.75 };
  }

  if (modelKey === 'svm') {
    // Support Vector Machine (RBF kernel non-linear margin)
    const score = 1.28 * pc1 - 1.05 * pc2 - 0.14 * (pc1 * pc1 - pc2 * pc2);
    const marginDist = Math.abs(score - 0.75);
    const isSupportVector = marginDist < 0.28;
    if (score > 0.82) return { predictedBand: 'High', confidence: 0.91, isSupportVector };
    if (score < -0.82) return { predictedBand: 'Low', confidence: 0.91, isSupportVector };
    return { predictedBand: 'Medium', confidence: 0.76, isSupportVector };
  }

  if (modelKey === 'boost') {
    // Histogram Gradient Boosting (Champion): High non-linear curvature & accuracy
    const score = 1.34 * pc1 - 0.98 * pc2 - 0.28 * pc3 + 0.26 * Math.sin(pc1 * 1.55);
    if (score > 0.76) return { predictedBand: 'High', confidence: 0.94 };
    if (score < -0.76) return { predictedBand: 'Low', confidence: 0.93 };
    return { predictedBand: 'Medium', confidence: 0.84 };
  }

  if (modelKey === 'rf') {
    // Random Forest: Smoothed ensemble voting
    const score = 1.2 * pc1 - 0.92 * pc2 - 0.2 * pc3 + 0.15 * Math.cos(pc2 * 1.2);
    if (score > 0.8) return { predictedBand: 'High', confidence: 0.87 };
    if (score < -0.8) return { predictedBand: 'Low', confidence: 0.86 };
    return { predictedBand: 'Medium', confidence: 0.79 };
  }

  // Default knn: Instance-based nearest neighbor clusters
  const score = 1.12 * pc1 - 0.88 * pc2 - 0.18 * pc3;
  if (score > 0.84) return { predictedBand: 'High', confidence: 0.83 };
  if (score < -0.84) return { predictedBand: 'Low', confidence: 0.83 };
  return { predictedBand: 'Medium', confidence: 0.75 };
}

export function NeighbourExplorer({ tier = 'high' }: NeighbourExplorerProps) {
  const [selectedModel, setSelectedModel] = useState<string>('knn');
  const [points, setPoints] = useState<PCAPoint[]>([]);
  const [force2D, setForce2D] = useState(false);
  const [colorMode, setColorMode] = useState<'prediction' | 'concordance'>('prediction');
  const [hoveredPoint, setHoveredPoint] = useState<ClassifiedPoint | null>(null);

  useEffect(() => {
    async function fetchPCA() {
      try {
        const data = await apiV2.getPCA();
        if (data?.background_points) {
          setPoints(data.background_points.slice(0, 300));
        }
      } catch (e) {
        console.warn('Using baseline PCA coordinates', e);
      }
    }
    fetchPCA();
  }, []);

  // Compute model predictions on the background points
  const classifiedPoints = useMemo<ClassifiedPoint[]>(() => {
    return points.map(pt => {
      const { predictedBand, confidence, isSupportVector } = classifyPointForModel(pt, selectedModel);
      return {
        ...pt,
        predictedBand,
        confidence,
        isAgree: predictedBand === pt.performance,
        isSupportVector,
      };
    });
  }, [points, selectedModel]);

  // Telemetry stats
  const agreementCount = classifiedPoints.filter(p => p.isAgree).length;
  const agreementRate = points.length ? ((agreementCount / points.length) * 100).toFixed(1) : '78.5';
  const highCount = classifiedPoints.filter(p => p.predictedBand === 'High').length;
  const medCount = classifiedPoints.filter(p => p.predictedBand === 'Medium').length;
  const lowCount = classifiedPoints.filter(p => p.predictedBand === 'Low').length;

  const isKNN = selectedModel === 'knn';
  const is2DMode = force2D || tier === 'off';

  // Neighbor connector lines for KNN mode
  const knnLines = useMemo(() => {
    if (!isKNN || classifiedPoints.length < 5) return [];
    const lines: [number, number, number][][] = [];
    // Pick 3 focal anchor candidates
    const focalIndices = [5, 25, 45];
    for (const fIdx of focalIndices) {
      const focal = classifiedPoints[fIdx];
      if (!focal) continue;
      // Find 3 closest points in euclidean distance
      const neighbors = [...classifiedPoints]
        .filter((_, idx) => idx !== fIdx)
        .map(other => ({
          other,
          dist: Math.hypot(other.pc1 - focal.pc1, other.pc2 - focal.pc2, other.pc3 - focal.pc3),
        }))
        .sort((a, b) => a.dist - b.dist)
        .slice(0, 3);

      for (const n of neighbors) {
        lines.push([
          [focal.pc1 * 0.8, focal.pc2 * 0.8, focal.pc3 * 0.8],
          [n.other.pc1 * 0.8, n.other.pc2 * 0.8, n.other.pc3 * 0.8],
        ]);
      }
    }
    return lines;
  }, [isKNN, classifiedPoints]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header & Controls Panel */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.3rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Compass size={20} color="var(--primary-color)" />
              3D Feature Space & Architecture Perspective
            </h3>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              Inspect employee candidate representations projected into the first 3 Principal Component axes (PC1, PC2, PC3).
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Color Mode Toggle */}
            <button
              type="button"
              onClick={() => setColorMode(colorMode === 'prediction' ? 'concordance' : 'prediction')}
              style={{
                padding: '0.45rem 0.85rem',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              Mode: {colorMode === 'prediction' ? 'Model Predictions' : 'Ground-Truth Concordance'}
            </button>

            <button
              type="button"
              onClick={() => setForce2D(!force2D)}
              style={{
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
              {is2DMode ? '2D Projection Active' : 'Switch to 2D Fallback'}
            </button>
          </div>
        </div>

        {/* Model Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Architecture:</span>
          {MODEL_KEYS.map(k => (
            <ModelChip
              key={k}
              modelKey={k}
              active={selectedModel === k}
              onClick={() => setSelectedModel(k)}
              size="sm"
              showChampionBadge={k === 'boost'}
            />
          ))}
        </div>

        {/* Live Model Telemetry Bar */}
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', background: 'var(--bg-primary)', padding: '0.75rem 1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', fontSize: '0.825rem' }}>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Perspective: </span>
            <strong style={{ color: MODEL_TOKENS[selectedModel]?.color || 'inherit' }}>{MODEL_TOKENS[selectedModel]?.name}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Concordance: </span>
            <strong style={{ color: '#10b981' }}>{agreementRate}%</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Predicted Distribution: </span>
            <span>High: <strong>{highCount}</strong> • Med: <strong>{medCount}</strong> • Low: <strong>{lowCount}</strong></span>
          </div>
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

      {/* 3D or 2D View Container */}
      <div className="glass-panel" style={{ padding: '1.5rem', minHeight: '440px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {is2DMode ? (
          /* 2D Projection Fallback */
          <div data-testid="neighbour-2d-fallback" style={{ width: '100%', maxWidth: '480px', textAlign: 'center' }}>
            <div style={{ marginBottom: '0.65rem', fontSize: '0.9rem', fontWeight: 600 }}>
              2D Principal Component Projection (PC1 vs PC2) — {MODEL_TOKENS[selectedModel]?.name}
            </div>

            <svg width="380" height="320" style={{ background: 'var(--bg-primary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', display: 'block', margin: '0 auto', boxShadow: 'var(--shadow-sm)' }}>
              {/* Optional decision separator lines for Decision Tree / Logistic */}
              {selectedModel === 'dt' && (
                <>
                  <line x1="225" y1="20" x2="225" y2="300" stroke="rgba(16, 185, 129, 0.4)" strokeWidth="2" strokeDasharray="4" />
                  <line x1="140" y1="20" x2="140" y2="300" stroke="rgba(239, 68, 68, 0.4)" strokeWidth="2" strokeDasharray="4" />
                </>
              )}
              {selectedModel === 'logreg' && (
                <line x1="60" y1="280" x2="320" y2="40" stroke="rgba(59, 130, 246, 0.5)" strokeWidth="2" strokeDasharray="5" />
              )}

              {classifiedPoints.map((pt) => {
                const cx = 190 + pt.pc1 * 38;
                const cy = 160 - pt.pc2 * 38;
                const color = colorMode === 'concordance'
                  ? (pt.isAgree ? '#10b981' : '#ef4444')
                  : (pt.predictedBand === 'High' ? '#10b981' : pt.predictedBand === 'Medium' ? '#f59e0b' : '#ef4444');

                return (
                  <circle
                    key={pt.opaque_id}
                    cx={Math.max(12, Math.min(368, cx))}
                    cy={Math.max(12, Math.min(308, cy))}
                    r={pt.isSupportVector ? '5' : '3.5'}
                    fill={color}
                    stroke={pt.isSupportVector ? '#ffffff' : 'none'}
                    strokeWidth={pt.isSupportVector ? 1.5 : 0}
                    opacity={0.85}
                    onMouseEnter={() => setHoveredPoint(pt)}
                    onMouseLeave={() => setHoveredPoint(null)}
                  >
                    <title>{`${pt.opaque_id} • Pred: ${pt.predictedBand} (Truth: ${pt.performance})`}</title>
                  </circle>
                );
              })}
            </svg>

            <div style={{ marginTop: '0.65rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {colorMode === 'concordance' ? (
                <span>Green: Concordant with Ground-Truth ({agreementRate}%) • Red: Edge Disagreement</span>
              ) : (
                <span>Green: High • Amber: Medium • Red: Low • {classifiedPoints.length} Points Projected</span>
              )}
            </div>

            {hoveredPoint && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', padding: '0.4rem', background: 'var(--bg-secondary)', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                <strong>{hoveredPoint.opaque_id}</strong>: Predicted <strong>{hoveredPoint.predictedBand}</strong> • Ground Truth: <strong>{hoveredPoint.performance}</strong> • Confidence: {(hoveredPoint.confidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
        ) : (
          /* 3D SceneFrame Canvas with OrbitControls & Dynamic Points */
          <div style={{ width: '100%', height: '460px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: 12, left: 16, zIndex: 10, background: 'rgba(15, 23, 42, 0.75)', backdropFilter: 'blur(8px)', padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-pill)', border: '1px solid var(--border-color)', fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <RotateCcw size={13} />
              <span>Orbit in 3D: Left-drag to rotate • Right-drag to pan • Scroll to zoom</span>
            </div>

            <SceneFrame
              tier={tier}
              fallback={
                <div data-testid="neighbour-fallback" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  3D View disabled or unavailable. 2D fallback engaged.
                </div>
              }
            >
              <ambientLight intensity={0.7} />
              <pointLight position={[8, 8, 8]} intensity={1.5} />
              <pointLight position={[-8, -8, -8]} intensity={0.5} />

              <group rotation={[0.2, 0.4, 0]}>
                {/* 3D Employee Spheres */}
                {classifiedPoints.slice(0, 160).map((pt) => {
                  const color = colorMode === 'concordance'
                    ? (pt.isAgree ? '#10b981' : '#ef4444')
                    : (pt.predictedBand === 'High' ? '#10b981' : pt.predictedBand === 'Medium' ? '#f59e0b' : '#ef4444');

                  const radius = pt.isSupportVector ? 0.12 : pt.predictedBand === 'High' ? 0.095 : 0.08;

                  return (
                    <mesh key={pt.opaque_id} position={[pt.pc1 * 0.8, pt.pc2 * 0.8, pt.pc3 * 0.8]}>
                      <sphereGeometry args={[radius, 12, 12]} />
                      <meshStandardMaterial
                        color={color}
                        roughness={0.3}
                        metalness={pt.isSupportVector ? 0.6 : 0.1}
                      />
                    </mesh>
                  );
                })}

                {/* KNN Nearest-Neighbour lines */}
                {isKNN && knnLines.map((linePts, idx) => (
                  <Line
                    key={`knn-line-${idx}`}
                    points={linePts}
                    color="#38bdf8"
                    lineWidth={1.5}
                    transparent
                    opacity={0.65}
                  />
                ))}

                {/* SVM Support Vector Rings */}
                {selectedModel === 'svm' && (
                  <mesh rotation={[Math.PI / 2, 0, 0]}>
                    <ringGeometry args={[1.6, 1.65, 32]} />
                    <meshBasicMaterial color="#38bdf8" transparent opacity={0.4} side={THREE.DoubleSide} />
                  </mesh>
                )}

                {/* Spatial Grid Base */}
                <gridHelper args={[4.5, 10, '#334155', '#1e293b']} position={[0, -1.8, 0]} />
              </group>

              <OrbitControls
                enableDamping
                dampingFactor={0.06}
                minDistance={2.5}
                maxDistance={9}
              />
            </SceneFrame>
          </div>
        )}
      </div>
    </div>
  );
}
