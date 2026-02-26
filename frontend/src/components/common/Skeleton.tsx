/**
 * Skeleton — animated placeholder for loading states.
 */

import React from 'react';

interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
}

export function Skeleton({ className = '', width, height }: SkeletonProps): React.ReactElement {
  return (
    <div
      className={`animate-pulse rounded-md bg-bg-hover ${className}`}
      style={{ width, height }}
      role="status"
      aria-label="Loading"
    />
  );
}
