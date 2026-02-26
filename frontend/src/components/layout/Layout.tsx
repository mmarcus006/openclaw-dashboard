/**
 * Layout — sidebar + header + connection banner + main content area.
 */

import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ConnectionBanner } from '@/components/common/ConnectionBanner';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  noPadding?: boolean;
}

export function Layout({ children, title, noPadding }: LayoutProps): React.ReactElement {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header title={title} />
        <ConnectionBanner />
        <main className={`flex-1 overflow-auto ${noPadding ? '' : 'p-6'}`}>
          {children}
        </main>
      </div>
    </div>
  );
}
