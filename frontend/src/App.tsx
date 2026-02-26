/**
 * App — root with RouterProvider + ToastContainer + WebSocket initializer.
 * WsInitializer is mounted once here; singleton logic in useWebSocket
 * ensures only one connection is ever created.
 */

import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import { ToastContainer } from '@/components/common/Toast';
import { useWebSocket } from '@/hooks/useWebSocket';

/**
 * Mounts the singleton WebSocket connection at app root (sibling of RouterProvider).
 * Singleton logic in useWebSocket ensures only one connection is ever created.
 * Renders null — only here for the useEffect in useWebSocket.
 */
function WsInitializer(): null {
  useWebSocket();
  return null;
}

function AppContent(): React.ReactElement {
  return (
    <>
      <WsInitializer />
      <RouterProvider router={router} />
      <ToastContainer />
    </>
  );
}

export function App(): React.ReactElement {
  return <AppContent />;
}
