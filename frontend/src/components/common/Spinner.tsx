/**
 * Spinner — loading indicator.
 */

import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

const SIZE_CLASSES = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-[3px]',
};

export function Spinner({ size = 'md', className = '', label = 'Loading…' }: SpinnerProps): React.ReactElement {
  return (
    <div
      role="status"
      aria-label={label}
      className={`${SIZE_CLASSES[size]} border-bg-hover border-t-accent rounded-full animate-spin ${className}`}
    />
  );
}

export function FullPageSpinner(): React.ReactElement {
  return (
    <div className="flex items-center justify-center h-full min-h-32">
      <Spinner size="lg" />
    </div>
  );
}
