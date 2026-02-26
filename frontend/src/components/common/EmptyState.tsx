/**
 * EmptyState — consistent icon + title + description + optional action.
 */

import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = '',
}: EmptyStateProps): React.ReactElement {
  return (
    <div className={`flex flex-col items-center justify-center py-12 text-center ${className}`}>
      <div className="text-text-tertiary mb-3">
        {icon ?? <Inbox size={40} />}
      </div>
      <h3 className="text-text-primary font-medium text-sm mb-1">{title}</h3>
      {description && <p className="text-text-secondary text-xs max-w-xs">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
