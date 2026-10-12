import { useState } from 'react';
import SceneFrame from './SceneFrame';
import { Play, Pause } from 'lucide-react';

interface TalentGalaxyProps {
  tier?: 'high' | 'off';
  onTierChange?: (tier: 'high' | 'off') => void;
}

export function TalentGalaxy({ tier = 'high' }: TalentGalaxyProps) {
  const [paused, setPaused] = useState(false);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.25rem' }}>Talent Galaxy Interactive Hero</h3>
          <p style={{ margin: '0.2rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Multi-dimensional employee talent universe rendered via WebGL with pause and accessibility controls.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            type="button"
            onClick={() => setPaused(!paused)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0.4rem 0.8rem',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: 600,
            }}
          >
            {paused ? <Play size={14} /> : <Pause size={14} />}
            {paused ? 'Resume Motion' : 'Pause Orbit'}
          </button>
        </div>
      </div>

      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', minHeight: '420px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {tier === 'off' ? (
          <div data-testid="galaxy-fallback" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            3D Talent Galaxy is paused or disabled under quality settings.
          </div>
        ) : (
          <div style={{ width: '100%', height: '400px' }}>
            <SceneFrame
              tier={tier}
              fallback={
                <div data-testid="galaxy-fallback" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  3D Engine unavailable or reduced motion active.
                </div>
              }
            >
              <ambientLight intensity={0.5} />
              <pointLight position={[10, 10, 10]} intensity={1.5} />

              <group rotation={paused ? [0.3, 0.3, 0] : [0.5, 0.8, 0]}>
                <mesh position={[0, 0, 0]}>
                  <sphereGeometry args={[1.2, 32, 32]} />
                  <meshStandardMaterial color="#3b82f6" roughness={0.3} wireframe={true} />
                </mesh>
                <mesh position={[2, 1, -1]}>
                  <sphereGeometry args={[0.3, 16, 16]} />
                  <meshStandardMaterial color="#10b981" />
                </mesh>
                <mesh position={[-2, -1, 1]}>
                  <sphereGeometry args={[0.25, 16, 16]} />
                  <meshStandardMaterial color="#f59e0b" />
                </mesh>
                <mesh position={[1, -2, -0.5]}>
                  <sphereGeometry args={[0.35, 16, 16]} />
                  <meshStandardMaterial color="#D55E00" />
                </mesh>
              </group>
            </SceneFrame>
          </div>
        )}
      </div>
    </div>
  );
}
