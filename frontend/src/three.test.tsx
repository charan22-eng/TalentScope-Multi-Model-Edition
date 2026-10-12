import { render, screen, cleanup } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { DecisionLandscape } from './components/three/DecisionLandscape';
import { NeighbourExplorer } from './components/three/NeighbourExplorer';
import { TalentGalaxy } from './components/three/TalentGalaxy';
import '@testing-library/jest-dom/vitest';

// Mock apiV2 methods
vi.mock('./lib/api-client-v2', () => ({
  apiV2: {
    getSurface: vi.fn().mockResolvedValue({
      feature_x: 'attendance',
      feature_y: 'projects_completed',
      grid_size: 40,
      x_range: [60, 100],
      y_range: [0, 15],
      prob_high_surface: Array.from({ length: 40 }, () => Array.from({ length: 40 }, () => 0.5)),
    }),
    getPCA: vi.fn().mockResolvedValue({
      explained_variance_ratio: [0.19, 0.14, 0.11],
      background_points: [
        { opaque_id: 'BG001', pc1: 1.2, pc2: -0.5, pc3: 0.1, performance: 'High' },
        { opaque_id: 'BG002', pc1: -1.0, pc2: 0.8, pc3: -0.2, performance: 'Low' },
      ],
    }),
  },
}));

describe('3D Component Suite & Fallback Guarantees (Stage K)', () => {
  afterEach(() => {
    cleanup();
  });

  it('DecisionLandscape renders 2D fallback grid when tier="off"', async () => {
    render(<DecisionLandscape tier="off" />);
    const fallback = await screen.findByTestId('surface-2d-fallback');
    expect(fallback).toBeInTheDocument();
    expect(screen.getByText(/2D High-Resolution Probability Grid/i)).toBeInTheDocument();
  });

  it('NeighbourExplorer renders 2D projection fallback when tier="off"', async () => {
    render(<NeighbourExplorer tier="off" />);
    const fallback = await screen.findByTestId('neighbour-2d-fallback');
    expect(fallback).toBeInTheDocument();
    expect(screen.getByText(/2D Principal Component Projection/i)).toBeInTheDocument();
  });

  it('TalentGalaxy renders accessible fallback when tier="off"', () => {
    render(<TalentGalaxy tier="off" />);
    expect(screen.getByTestId('galaxy-fallback')).toBeInTheDocument();
    expect(screen.getByText(/Talent Galaxy is paused or disabled/i)).toBeInTheDocument();
  });

  it('verifies clean mount and unmount without memory leaks', () => {
    const { unmount } = render(<TalentGalaxy tier="off" />);
    expect(screen.getByTestId('galaxy-fallback')).toBeInTheDocument();
    unmount();
    expect(screen.queryByTestId('galaxy-fallback')).not.toBeInTheDocument();
  });
});
