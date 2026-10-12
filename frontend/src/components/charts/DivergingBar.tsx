import React from 'react';

interface DivergingBarProps {
  label: string;
  value: number; // between -1 and +1, or difference
  leftLabel?: string;
  rightLabel?: string;
  leftColor?: string;
  rightColor?: string;
  maxAbsValue?: number;
}

export const DivergingBar: React.FC<DivergingBarProps> = ({
  label,
  value,
  leftLabel = 'Favors Model A',
  rightLabel = 'Favors Model B',
  leftColor = '#56B4E9',
  rightColor = '#D55E00',
  maxAbsValue = 0.2,
}) => {
  const normVal = Math.max(-maxAbsValue, Math.min(maxAbsValue, value));
  const widthPct = (Math.abs(normVal) / maxAbsValue) * 50;
  const isPositive = normVal >= 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', width: '100%', margin: '0.4rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
        <span>{label}</span>
        <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>
          {isPositive ? `+${value.toFixed(4)}` : value.toFixed(4)}
        </span>
      </div>

      <div
        style={{
          position: 'relative',
          height: '16px',
          background: 'var(--bg-secondary, #1e293b)',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {/* Center line */}
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: 0,
            bottom: 0,
            width: '2px',
            background: 'var(--border-color, #475569)',
            zIndex: 1,
          }}
        />

        {/* Bar */}
        {isPositive ? (
          <div
            style={{
              position: 'absolute',
              left: '50%',
              width: `${widthPct}%`,
              height: '100%',
              background: rightColor,
              borderRadius: '0 3px 3px 0',
            }}
            title={`${rightLabel}: +${value.toFixed(4)}`}
          />
        ) : (
          <div
            style={{
              position: 'absolute',
              right: '50%',
              width: `${widthPct}%`,
              height: '100%',
              background: leftColor,
              borderRadius: '3px 0 0 3px',
            }}
            title={`${leftLabel}: ${value.toFixed(4)}`}
          />
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
        <span>← {leftLabel}</span>
        <span>{rightLabel} →</span>
      </div>
    </div>
  );
};
