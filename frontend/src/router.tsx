/**
 * Router — all routes.
 * EditorPage is lazy-loaded (Monaco bundle is 2.5MB). (R4)
 * Other pages are small enough to eager-load.
 */

import React, { lazy, Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { FullPageSpinner } from '@/components/common/Spinner';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

// Eager-loaded pages (small)
import DashboardPage from '@/pages/DashboardPage';
import AgentsPage from '@/pages/AgentsPage';
import AgentPage from '@/pages/AgentPage';
import GatewayPage from '@/pages/GatewayPage';
import ConfigPage from '@/pages/ConfigPage';

// Lazy-loaded — Monaco is 2.5MB (R4 — MANDATORY)
const EditorPage = lazy(() => import('@/pages/EditorPage'));

function LazyEditorPage(): React.ReactElement {
  return (
    <ErrorBoundary label="Editor failed to load">
      <Suspense fallback={<FullPageSpinner />}>
        <EditorPage />
      </Suspense>
    </ErrorBoundary>
  );
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <DashboardPage />,
  },
  {
    path: '/agents',
    element: <AgentsPage />,
  },
  {
    path: '/agents/:agentId',
    element: <AgentPage />,
  },
  {
    path: '/editor',
    element: <LazyEditorPage />,
  },
  {
    path: '/config',
    element: <ConfigPage />,
  },
  {
    path: '/gateway',
    element: <GatewayPage />,
  },
]);
