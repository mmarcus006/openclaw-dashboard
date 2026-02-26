/**
 * GatewayPage — gateway controls + cron job viewer.
 */

import React from 'react';
import { Layout } from '@/components/layout/Layout';
import { GatewayPanel } from '@/components/gateway/GatewayPanel';
import { CronJobList } from '@/components/gateway/CronJobList';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

export default function GatewayPage(): React.ReactElement {
  return (
    <Layout title="Gateway">
      <div className="max-w-4xl space-y-6">
        <ErrorBoundary label="Gateway panel error">
          <GatewayPanel />
        </ErrorBoundary>
        <ErrorBoundary label="Cron jobs error">
          <CronJobList />
        </ErrorBoundary>
      </div>
    </Layout>
  );
}
