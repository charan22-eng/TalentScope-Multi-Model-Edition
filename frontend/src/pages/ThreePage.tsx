import { useState } from 'react';
import { DecisionLandscape } from '../components/three/DecisionLandscape';
import { NeighbourExplorer } from '../components/three/NeighbourExplorer';
import { TalentGalaxy } from '../components/three/TalentGalaxy';
import { Layers, Compass, Sparkles } from 'lucide-react';

export default function ThreePage() {
  const [activeTab, setActiveTab] = useState<'landscape' | 'neighbour' | 'galaxy'>('landscape');
  const [tier, setTier] = useState<'high' | 'off'>('high');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1rem 0' }}>
      {/* Modern Glassmorphic Tab Navigation */}
      <div
        className="glass-panel"
        style={{
          display: 'flex',
          gap: '0.6rem',
          padding: '0.65rem 0.85rem',
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('landscape')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.1rem',
            borderRadius: 'var(--radius)',
            border: activeTab === 'landscape' ? '1px solid var(--primary-color)' : '1px solid transparent',
            background: activeTab === 'landscape' ? 'var(--primary-action)' : 'transparent',
            color: activeTab === 'landscape' ? '#ffffff' : 'var(--text-secondary)',
            fontWeight: activeTab === 'landscape' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '0.875rem',
            boxShadow: activeTab === 'landscape' ? 'var(--shadow-glow)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          <Layers size={17} />
          <span>Decision Landscape (3D / 2D)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('neighbour')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.1rem',
            borderRadius: 'var(--radius)',
            border: activeTab === 'neighbour' ? '1px solid var(--primary-color)' : '1px solid transparent',
            background: activeTab === 'neighbour' ? 'var(--primary-action)' : 'transparent',
            color: activeTab === 'neighbour' ? '#ffffff' : 'var(--text-secondary)',
            fontWeight: activeTab === 'neighbour' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '0.875rem',
            boxShadow: activeTab === 'neighbour' ? 'var(--shadow-glow)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          <Compass size={17} />
          <span>3D Neighbour Explorer (PCA)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('galaxy')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.1rem',
            borderRadius: 'var(--radius)',
            border: activeTab === 'galaxy' ? '1px solid var(--primary-color)' : '1px solid transparent',
            background: activeTab === 'galaxy' ? 'var(--primary-action)' : 'transparent',
            color: activeTab === 'galaxy' ? '#ffffff' : 'var(--text-secondary)',
            fontWeight: activeTab === 'galaxy' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '0.875rem',
            boxShadow: activeTab === 'galaxy' ? 'var(--shadow-glow)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          <Sparkles size={17} />
          <span>Talent Galaxy Hero Scene</span>
        </button>
      </div>

      {activeTab === 'landscape' && <DecisionLandscape tier={tier} onTierChange={setTier} />}
      {activeTab === 'neighbour' && <NeighbourExplorer tier={tier} onTierChange={setTier} />}
      {activeTab === 'galaxy' && <TalentGalaxy tier={tier} onTierChange={setTier} />}
    </div>
  );
}
