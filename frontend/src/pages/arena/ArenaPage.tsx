import { useState } from 'react';
import { ArenaOverview } from './ArenaOverview';
import { ArenaPriorities } from './ArenaPriorities';
import { ArenaHeadToHead } from './ArenaHeadToHead';
import { ArenaMetricsDeepDive } from './ArenaMetricsDeepDive';
import { ArenaCostSpeed } from './ArenaCostSpeed';
import { ArenaSensitivity } from './ArenaSensitivity';
import { ArenaExplainability } from './ArenaExplainability';
import { ArenaFairnessRobustness } from './ArenaFairnessRobustness';
import { ArenaLLMVerdict } from './ArenaLLMVerdict';
import {
  Trophy,
  Sliders,
  GitCompare,
  Activity,
  Zap,
  GitBranch,
  Sparkles,
  ShieldCheck,
  FileText,
} from 'lucide-react';

export default function ArenaPage() {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Trophy },
    { id: 'priorities', label: 'Priorities (MCDA)', icon: Sliders },
    { id: 'head2head', label: 'Head-to-Head', icon: GitCompare },
    { id: 'metrics', label: 'Metrics Deep Dive', icon: Activity },
    { id: 'cost-speed', label: 'Cost & Speed', icon: Zap },
    { id: 'sensitivity', label: 'Data Sensitivity', icon: GitBranch },
    { id: 'explain', label: 'Explainability', icon: Sparkles },
    { id: 'fairness', label: 'Fairness & Robustness', icon: ShieldCheck },
    { id: 'llm', label: 'LLM Verdict', icon: FileText },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1rem 0' }}>
      <h1 className="sr-only">TalentScope Model Arena</h1>
      {/* Modern Glassmorphic Sub-Tabs Navigation */}
      <div
        className="glass-panel"
        style={{
          display: 'flex',
          gap: '0.45rem',
          overflowX: 'auto',
          padding: '0.6rem 0.8rem',
        }}
      >
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveTab(t.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.55rem 0.95rem',
                borderRadius: 'var(--radius-pill)',
                border: isActive ? '1px solid var(--primary-color)' : '1px solid transparent',
                background: isActive ? 'var(--primary-action)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.85rem',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                boxShadow: isActive ? 'var(--shadow-glow)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              <Icon size={15} color={isActive ? '#ffffff' : undefined} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Render Active Sub-View */}
      {activeTab === 'overview' && <ArenaOverview onNavigateToTab={setActiveTab} />}
      {activeTab === 'priorities' && <ArenaPriorities />}
      {activeTab === 'head2head' && <ArenaHeadToHead />}
      {activeTab === 'metrics' && <ArenaMetricsDeepDive />}
      {activeTab === 'cost-speed' && <ArenaCostSpeed />}
      {activeTab === 'sensitivity' && <ArenaSensitivity />}
      {activeTab === 'explain' && <ArenaExplainability />}
      {activeTab === 'fairness' && <ArenaFairnessRobustness />}
      {activeTab === 'llm' && <ArenaLLMVerdict />}
    </div>
  );
}
