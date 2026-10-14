import React from 'react';
import { MODEL_TOKENS } from '../../lib/tokens';

interface CIWhiskerProps {
  modelKey: string;
  point: number;
  ciLow: number;
  ciHigh: number;
  minScale?: number;
  maxScale?: number;
  metricName?: string;
  format?: (v: number) => string;
}

export const CIWhisker: React.FC<CIWhiskerProps> = ({
  modelKey,
  point,
  ciLow,
  ciHigh,
  minScale = 0.5,
  maxScale = 1.0,
  metricName = 'Macro-F1',
  format = (v: number) => (v !== undefined && v !== null ? v.toFixed(3) : '0.000'),
}) => {
  const token = MODEL_TOKENS[modelKey] || {
    name: modelKey,
    color: '#3b82f6',
    marker: '●',
  };

  const scaleRange = Math.max(maxScale - minScale, 0.001);
  const toPct = (val: number) => {
    const clamped = Math.max(minScale, Math.min(maxScale, val));
    return ((clamped - minScale) / scaleRange) * 100;
  };

  const leftPct = toPct(ciLow);
  const rightPct = toPct(ciHigh);
  const centerPct = toPct(point);

  return (
    <div
      role="group"
      aria-label={`${token.name} ${metricName}: ${format(point)} (95% CI ${format(ciLow)} to ${format(ciHigh)})`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.4rem 0',
        width: '100%',
      }}
    >
      <div style={{ width: '130px', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>
        <span style={{ color: token.color, marginRight: '6px' }}>{token.marker}</span>
        {token.name.replace(' (Champion)', '')}
      </div>

      <div style={{ flex: 1, position: 'relative', height: '24px', display: 'flex', alignItems: 'center' }}>
        {/* Background track */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            height: '2px',
            background: 'var(--border-color, #334155)',
          }}
        />

        {/* CI Interval Line */}
        <div
          style={{
            position: 'absolute',
            left: `${leftPct}%`,
            width: `${Math.max(rightPct - leftPct, 0.5)}%`,
            height: '4px',
            background: token.color,
            borderRadius: '2px',
          }}
        />

        {/* Left Whisker End Cap */}
        <div
          style={{
            position: 'absolute',
            left: `${leftPct}%`,
            top: '4px',
            bottom: '4px',
            width: '2px',
            background: token.color,
          }}
        />

        {/* Right Whisker End Cap */}
        <div
          style={{
            position: 'absolute',
            left: `${rightPct}%`,
            top: '4px',
            bottom: '4px',
            width: '2px',
            background: token.color,
          }}
        />

        {/* Point Estimate Marker */}
        <div
          style={{
            position: 'absolute',
            left: `${centerPct}%`,
            transform: 'translateX(-50%)',
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            background: token.color,
            border: '2px solid var(--bg-primary, #0f172a)',
            boxShadow: '0 0 4px rgba(0,0,0,0.4)',
          }}
          title={`Point: ${format(point)}`}
        />
      </div>

      <div
        style={{
          width: '120px',
          textAlign: 'right',
          fontFamily: 'monospace',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
        }}
      >
        <strong>{format(point)}</strong> [{format(ciLow)}, {format(ciHigh)}]
      </div>
    </div>
  );
};
