/**
 * Badge — colored pill for model names and status labels.
 */

import React from 'react';

export type BadgeVariant = 'accent' | 'success' | 'warning' | 'danger' | 'neutral';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  accent: 'bg-accent/20 text-[#a5b4fc] border border-accent/30',
  success: 'bg-success/20 text-success border border-success/30',
  warning: 'bg-warning/20 text-warning-contrast border border-warning/30',
  danger: 'bg-danger/20 text-danger border border-danger/30',
  neutral: 'bg-bg-hover text-text-secondary border border-border',
};

export function Badge({ children, variant = 'neutral', className = '' }: BadgeProps): React.ReactElement {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${VARIANT_CLASSES[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

/** Map agent status to badge variant */
export function statusVariant(status: string): BadgeVariant {
  switch (status) {
    case 'active': return 'success';
    case 'idle': return 'warning';
    case 'stopped': return 'neutral';
    default: return 'neutral';
  }
}
