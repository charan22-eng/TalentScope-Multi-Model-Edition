import React from 'react';
import { MODEL_TOKENS, type ModelToken } from '../../lib/tokens';
import { Trophy } from 'lucide-react';

interface ModelChipProps {
  modelKey: string;
  active?: boolean;
  onClick?: () => void;
  showChampionBadge?: boolean;
  showTier?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ModelChip: React.FC<ModelChipProps> = ({
  modelKey,
  active = false,
  onClick,
  showChampionBadge,
  showTier = false,
  size = 'md',
  className = '',
}) => {
  const token: ModelToken = MODEL_TOKENS[modelKey] || {
    key: modelKey,
    name: modelKey.toUpperCase(),
    family: 'unknown',
    color: '#6b7280',
    marker: '■',
    markerShape: 'square',
    explainTier: 'model_agnostic',
  };

  const isInteractive = Boolean(onClick);
  const isChampionBadgeVisible = showChampionBadge !== undefined ? showChampionBadge : Boolean(token.isChampion);

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-sm gap-1.5',
    lg: 'px-3 py-1.5 text-base gap-2',
  }[size];

  return (
    <span
      role={isInteractive ? 'button' : 'status'}
      tabIndex={isInteractive ? 0 : undefined}
      onClick={onClick}
      onKeyDown={isInteractive ? (e) => (e.key === 'Enter' || e.key === ' ') && onClick?.() : undefined}
      aria-pressed={isInteractive ? active : undefined}
      aria-label={`Model: ${token.name}${isChampionBadgeVisible ? ' (Arena Champion)' : ''}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        borderRadius: '9999px',
        border: `2px solid ${active ? token.color : 'var(--border-color, #334155)'}`,
        background: active ? `${token.color}22` : 'var(--bg-secondary, #1e293b)',
        color: 'var(--text-primary, #f8fafc)',
        fontWeight: active ? 600 : 500,
        cursor: isInteractive ? 'pointer' : 'default',
        transition: 'all 0.15s ease',
      }}
      className={`model-chip ${sizeClasses} ${className}`}
    >
      {/* Distinct marker shape with Okabe-Ito color */}
      <span
        aria-hidden="true"
        style={{
          color: token.color,
          fontSize: size === 'sm' ? '0.75rem' : size === 'lg' ? '1.1rem' : '0.9rem',
          lineHeight: 1,
        }}
        title={`Shape: ${token.markerShape}`}
      >
        {token.marker}
      </span>

      <span className="model-chip-name">{token.name.replace(' (Champion)', '')}</span>

      {isChampionBadgeVisible && (
        <span
          title="Arena Champion (Balanced MCDA)"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '2px',
            background: 'var(--accent-warm-action)',
            color: '#ffffff',
            borderRadius: '9999px',
            padding: '1px 6px',
            fontSize: '0.65rem',
            fontWeight: 700,
            letterSpacing: '0.02em',
            textTransform: 'uppercase',
          }}
        >
          <Trophy size={10} aria-hidden="true" />
          Champion
        </span>
      )}

      {showTier && (
        <span
          title={`Explainability tier: ${token.explainTier}`}
          style={{
            fontSize: '0.65rem',
            padding: '1px 5px',
            borderRadius: '4px',
            background: 'var(--bg-primary, #0f172a)',
            color: 'var(--text-secondary, #94a3b8)',
            border: '1px solid var(--border-color, #334155)',
            textTransform: 'uppercase',
          }}
        >
          {token.explainTier}
        </span>
      )}
    </span>
  );
};
