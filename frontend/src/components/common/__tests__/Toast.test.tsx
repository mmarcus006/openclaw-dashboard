/**
 * Toast tests — auto-dismiss timing, stacking max 3.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { ToastContainer } from '../Toast';
import { useToastStore } from '@/stores/toastStore';

beforeEach(() => {
  useToastStore.setState({ toasts: [] });
  vi.useFakeTimers();
});

describe('Toast', () => {
  it('auto-dismisses after duration', () => {
    const { addToast } = useToastStore.getState();
    addToast('success', 'Test toast', 5000);

    render(<ToastContainer />);
    expect(screen.getByText('Test toast')).toBeInTheDocument();

    act(() => { vi.advanceTimersByTime(5000); });
    expect(screen.queryByText('Test toast')).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it('stacks max 3 toasts, drops oldest', () => {
    const { addToast } = useToastStore.getState();
    addToast('info', 'Toast 1');
    addToast('info', 'Toast 2');
    addToast('info', 'Toast 3');
    addToast('info', 'Toast 4');

    render(<ToastContainer />);
    expect(screen.queryByText('Toast 1')).not.toBeInTheDocument();
    expect(screen.getByText('Toast 2')).toBeInTheDocument();
    expect(screen.getByText('Toast 3')).toBeInTheDocument();
    expect(screen.getByText('Toast 4')).toBeInTheDocument();

    vi.useRealTimers();
  });
});
