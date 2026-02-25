/**
 * EditorPage — lazy-loaded Monaco editor.
 * The Monaco bundle is 2.5MB — MUST be lazy loaded. (R4)
 * React.lazy() import is in router.tsx, not here.
 */

import React, { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { FileEditor } from '@/components/editor/FileEditor';
import { useEditorStore } from '@/stores/editorStore';

function EditorPageContent(): React.ReactElement {
  const [searchParams] = useSearchParams();
  const agentId = searchParams.get('agent');
  const filePath = searchParams.get('path');

  const loadFile = useEditorStore((s) => s.loadFile);
  const currentFile = useEditorStore((s) => s.currentFile);

  useEffect(() => {
    if (agentId && filePath) {
      // Only load if different from what's currently open
      if (currentFile?.agentId !== agentId || currentFile?.path !== filePath) {
        void loadFile(agentId, filePath);
      }
    }
  }, [agentId, filePath, loadFile, currentFile]);

  return (
    // Error boundary specifically around Monaco (R4.5)
    <ErrorBoundary label="Editor crashed — Monaco error">
      <FileEditor />
    </ErrorBoundary>
  );
}

export default function EditorPage(): React.ReactElement {
  const [searchParams] = useSearchParams();
  const filePath = searchParams.get('path');

  return (
    <Layout title={filePath ? `Edit: ${filePath}` : 'Editor'}>
      <div className="h-full -m-6">
        <EditorPageContent />
      </div>
    </Layout>
  );
}
