import React from 'react';
import { MODEL_TOKENS } from '../../lib/tokens';

export interface VariantRanking {
  modelKey: string;
  linearRank: number;
  nonlinearRank: number;
  noisyRank: number;
}

interface BumpChartProps {
  rankings: VariantRanking[];
}

export const BumpChart: React.FC<BumpChartProps> = ({ rankings }) => {
  const variants = ['Linear', 'Nonlinear (Default)', 'Noisy Overlap'];
  const height = 300;
  const paddingY = 30;
  const rankCount = 7;
  const stepY = (height - 2 * paddingY) / (rankCount - 1);

  const getRankY = (rank: number) => paddingY + (rank - 1) * stepY;
  const xPositions = [80, 260, 440];

  return (
    <div style={{ width: '100%', overflowX: 'auto', background: 'var(--bg-secondary, #1e293b)', borderRadius: 'var(--radius)', padding: '1rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '0.5rem', fontWeight: 600 }}>
        Model Rank Movements Across Generator Variants
      </div>
      <p style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        Note: "No single model dominates in every data regime." Rankings shift depending on synthetic generator dynamics.
      </p>

      <svg width="520" height={height} style={{ display: 'block', margin: '0 auto' }} aria-label="Variant sensitivity bump chart">
        {/* Column Guides */}
        {xPositions.map((x, i) => (
          <g key={variants[i]}>
            <line x1={x} y1={paddingY} x2={x} y2={height - paddingY} stroke="var(--border-color, #475569)" strokeDasharray="3 3" />
            <text x={x} y={paddingY - 12} textAnchor="middle" fill="var(--text-primary)" fontSize="12" fontWeight="bold">
              {variants[i]}
            </text>
          </g>
        ))}

        {/* Lines for each model */}
        {rankings.map((r) => {
          const token = MODEL_TOKENS[r.modelKey] || { name: r.modelKey, color: '#94a3b8', marker: '●' };
          const y1 = getRankY(r.linearRank);
          const y2 = getRankY(r.nonlinearRank);
          const y3 = getRankY(r.noisyRank);

          const pathD = `M ${xPositions[0]} ${y1} C ${xPositions[0] + 90} ${y1}, ${xPositions[1] - 90} ${y2}, ${xPositions[1]} ${y2} C ${xPositions[1] + 90} ${y2}, ${xPositions[2] - 90} ${y3}, ${xPositions[2]} ${y3}`;

          return (
            <g key={r.modelKey}>
              <path
                d={pathD}
                fill="none"
                stroke={token.color}
                strokeWidth={token.key === 'rf' ? 4 : 2}
                opacity={0.9}
              />
              {/* Markers */}
              <circle cx={xPositions[0]} cy={y1} r={r.modelKey === 'rf' ? 6 : 4} fill={token.color} />
              <circle cx={xPositions[1]} cy={y2} r={r.modelKey === 'rf' ? 6 : 4} fill={token.color} />
              <circle cx={xPositions[2]} cy={y3} r={r.modelKey === 'rf' ? 6 : 4} fill={token.color} />

              {/* Labels on right */}
              <text
                x={xPositions[2] + 10}
                y={y3 + 4}
                fill={token.color}
                fontSize="11"
                fontWeight={token.key === 'rf' ? 'bold' : 'normal'}
              >
                #{r.noisyRank} {token.name.replace(' (Champion)', '')}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
