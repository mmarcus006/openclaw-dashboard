/**
 * Card — dark card container.
 */

import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function Card({ children, className = '', onClick, hoverable = false }: CardProps): React.ReactElement {
  const interactiveClasses = (hoverable || onClick)
    ? 'cursor-pointer hover:bg-bg-hover transition-colors hover:border-border'
    : '';

  return (
    <div
      className={`bg-bg-card border border-border rounded-lg p-4 ${interactiveClasses} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } } : undefined}
    >
      {children}
    </div>
  );
}
