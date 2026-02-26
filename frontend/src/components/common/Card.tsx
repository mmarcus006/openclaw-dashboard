/**
 * Card — dark card container.
 */

import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function Card({ children, className = '', onClick, hoverable = false, ...rest }: CardProps): React.ReactElement {
  const interactiveClasses = (hoverable || onClick)
    ? 'cursor-pointer hover:bg-bg-hover transition-all hover:border-border hover:shadow-[0_2px_8px_rgba(0,0,0,0.3)]'
    : '';

  return (
    <div
      {...rest}
      className={`bg-bg-card border border-border rounded-lg p-4 ${interactiveClasses} ${className}`}
      onClick={onClick}
      role={rest.role ?? (onClick ? 'button' : undefined)}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } } : undefined}
    >
      {children}
    </div>
  );
}
