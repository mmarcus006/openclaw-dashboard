/**
 * ErrorBoundary — catches render errors, shows fallback.
 * Wrap around: Monaco editor, page routes, gateway panel.
 */

import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from './Button';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  /** Optional label for error context in the UI */
  label?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error('[ErrorBoundary] Caught render error:', error, info);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  override render(): React.ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
          <AlertCircle className="text-danger" size={40} />
          <div>
            <h3 className="text-text-primary font-semibold mb-1">
              {this.props.label ?? 'Something went wrong'}
            </h3>
            <p className="text-text-secondary text-sm mb-4">
              {this.state.error?.message ?? 'An unexpected error occurred'}
            </p>
            <Button variant="secondary" size="sm" onClick={this.handleReset}>
              Try again
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
