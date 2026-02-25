/**
 * GatewayPage — gateway controls.
 */

import React from 'react';
import { Layout } from '@/components/layout/Layout';
import { GatewayPanel } from '@/components/gateway/GatewayPanel';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

export default function GatewayPage(): React.ReactElement {
  return (
    <Layout title="Gateway">
      <ErrorBoundary label="Gateway panel error">
        <GatewayPanel />
      </ErrorBoundary>
    </Layout>
  );
}
