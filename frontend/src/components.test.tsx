import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ClassChip } from './components/ui/ClassChip';
import '@testing-library/jest-dom/vitest';

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('ClassChip', () => {
  it('renders High chip with correct text and class', () => {
    render(<ClassChip status="High" />);
    const el = screen.getByRole('status');
    expect(el).toHaveClass('chip-high');
    expect(el).toHaveTextContent('High');
  });

  it('renders Unknown fallback', () => {
    // Testing component fallback behavior when receiving invalid/unexpected status value at runtime
    const invalidStatus = 'FooBar' as unknown as 'Low';
    render(<ClassChip status={invalidStatus} />);
    const el = screen.getByRole('status');
    expect(el).toHaveClass('chip-unknown');
    expect(el).toHaveTextContent('Unknown');
  });
});
