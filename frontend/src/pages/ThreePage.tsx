import { useState } from 'react';
import { DecisionLandscape } from '../components/three/DecisionLandscape';
import { NeighbourExplorer } from '../components/three/NeighbourExplorer';
import { TalentGalaxy } from '../components/three/TalentGalaxy';
import { Layers, Compass, Sparkles } from 'lucide-react';

export default function ThreePage() {
  const [activeTab, setActiveTab] = useState<'landscape' | 'neighbour' | 'galaxy'>('landscape');
  const [tier, setTier] = useState<'high' | 'off'>('high');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1.5rem 0' }}>
      {/* Tab Switcher */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        <button
          type="button"
          onClick={() => setActiveTab('landscape')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius)',
            border: `1px solid ${activeTab === 'landscape' ? 'var(--primary-color)' : 'var(--border-color)'}`,
            background: activeTab === 'landscape' ? 'var(--primary-color)' : 'var(--bg-secondary)',
            color: activeTab === 'landscape' ? '#ffffff' : 'var(--text-primary)',
            fontWeight: activeTab === 'landscape' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '0.85rem',
          }}
        >
          <Layers size={15} />
          Decision Landscape (3D / 2D)
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('neighbour')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius)',
            border: `1px solid ${activeTab === 'neighbour' ? 'var(--primary-color)' : 'var(--border-color)'}`,
            background: activeTab === 'neighbour' ? 'var(--primary-color)' : 'var(--bg-secondary)',
            color: activeTab === 'neighbour' ? '#ffffff' : 'var(--text-primary)',
            fontWeight: activeTab === 'neighbour' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '0.85rem',
          }}
        >
          <Compass size={15} />
          3D Neighbour Explorer (PCA)
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('galaxy')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius)',
            border: `1px solid ${activeTab === 'galaxy' ? 'var(--primary-color)' : 'var(--border-color)'}`,
            background: activeTab === 'galaxy' ? 'var(--primary-color)' : 'var(--bg-secondary)',
            color: activeTab === 'galaxy' ? '#ffffff' : 'var(--text-primary)',
            fontWeight: activeTab === 'galaxy' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '0.85rem',
          }}
        >
          <Sparkles size={15} />
          Talent Galaxy Hero Scene
        </button>
      </div>

      {activeTab === 'landscape' && <DecisionLandscape tier={tier} onTierChange={setTier} />}
      {activeTab === 'neighbour' && <NeighbourExplorer tier={tier} onTierChange={setTier} />}
      {activeTab === 'galaxy' && <TalentGalaxy tier={tier} onTierChange={setTier} />}
    </div>
  );
}
