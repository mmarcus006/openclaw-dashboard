/**
 * ConfigPage — openclaw.json editor.
 * ConfigEditor is also lazy-loaded since it uses Monaco.
 */

import React, { Suspense, lazy, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { FullPageSpinner } from '@/components/common/Spinner';
import { useConfigStore } from '@/stores/configStore';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';

// Lazy-load ConfigEditor (contains Monaco)
const ConfigEditor = lazy(() =>
  import('@/components/config/ConfigEditor').then((m) => ({ default: m.ConfigEditor })),
);

function ConfigPageContent(): React.ReactElement {
  const fetchConfig = useConfigStore((s) => s.fetchConfig);
  const content = useConfigStore((s) => s.content);

  useEffect(() => {
    if (!content) {
      void fetchConfig();
    }
  }, [fetchConfig, content]);

  return (
    <ErrorBoundary label="Config editor crashed">
      <Suspense fallback={<FullPageSpinner />}>
        <ConfigEditor />
      </Suspense>
    </ErrorBoundary>
  );
}

export default function ConfigPage(): React.ReactElement {
  useDocumentTitle('Config');

  return (
    <Layout title="Config">
      <div className="h-full -m-6">
        <ConfigPageContent />
      </div>
    </Layout>
  );
}
