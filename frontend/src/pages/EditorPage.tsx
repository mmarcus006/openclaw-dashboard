/**
 * EditorPage — file browser sidebar + Monaco editor.
 * Layout: [Sidebar 240px][Monaco flex-1]
 * Monaco is lazy-loaded (2.5MB). React.lazy() is in router.tsx.
 */

import React, { useEffect, useCallback, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { FileEdit, ChevronRight } from 'lucide-react';
import { Layout } from '@/components/layout/Layout';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { EmptyState } from '@/components/common/EmptyState';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { FileEditor } from '@/components/editor/FileEditor';
import { EditorSidebar } from '@/components/editor/EditorSidebar';
import { useEditorStore } from '@/stores/editorStore';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';

function Breadcrumb(): React.ReactElement | null {
  const currentFile = useEditorStore((s) => s.currentFile);
  const navigate = useNavigate();
  const [showNavConfirm, setShowNavConfirm] = useState(false);
  const [pendingNav, setPendingNav] = useState<string | null>(null);

  const handleBreadcrumbClick = useCallback(
    (path: string) => {
      if (currentFile?.dirty) {
        setPendingNav(path);
        setShowNavConfirm(true);
      } else {
        navigate(path);
      }
    },
    [currentFile?.dirty, navigate],
  );

  const confirmNav = useCallback(() => {
    if (pendingNav) {
      navigate(pendingNav);
    }
    setShowNavConfirm(false);
    setPendingNav(null);
  }, [pendingNav, navigate]);

  if (!currentFile) return null;

  return (
    <>
      <nav className="flex items-center gap-1.5 px-4 py-2 text-xs border-b border-border bg-bg-secondary">
        <button
          onClick={() => handleBreadcrumbClick('/agents')}
          className="text-text-secondary hover:text-accent transition-colors"
        >
          Agents
        </button>
        <ChevronRight size={12} className="text-text-tertiary" />
        <button
          onClick={() => handleBreadcrumbClick(`/agents/${currentFile.agentId}`)}
          className="text-text-secondary hover:text-accent transition-colors"
        >
          {currentFile.agentId}
        </button>
        <ChevronRight size={12} className="text-text-tertiary" />
        <span className="text-text-primary font-medium">
          {currentFile.path}
          {currentFile.dirty && (
            <span className="ml-1.5 text-warning" title="Unsaved changes">●</span>
          )}
        </span>
      </nav>

      <ConfirmDialog
        isOpen={showNavConfirm}
        onConfirm={confirmNav}
        onCancel={() => { setShowNavConfirm(false); setPendingNav(null); }}
        title="Unsaved changes"
        message="You have unsaved changes that will be lost if you navigate away. Continue?"
        confirmLabel="Leave page"
        cancelLabel="Stay"
        variant="warning"
      />
    </>
  );
}

function EditorPageContent(): React.ReactElement {
  const [searchParams] = useSearchParams();
  const agentId = searchParams.get('agent');
  const filePath = searchParams.get('path');

  const loadFile = useEditorStore((s) => s.loadFile);
  const currentFile = useEditorStore((s) => s.currentFile);

  useEffect(() => {
    if (agentId && filePath) {
      if (currentFile?.agentId !== agentId || currentFile?.path !== filePath) {
        void loadFile(agentId, filePath);
      }
    }
  }, [agentId, filePath, loadFile, currentFile]);

  if (!agentId || !filePath) {
    return (
      <EmptyState
        icon={<FileEdit size={40} />}
        title="Select a file to edit"
        description="Choose an agent and file from the sidebar to start editing."
        className="h-full"
      />
    );
  }

  return (
    <ErrorBoundary label="Editor crashed — Monaco error">
      <FileEditor />
    </ErrorBoundary>
  );
}

export default function EditorPage(): React.ReactElement {
  const currentFile = useEditorStore((s) => s.currentFile);
  const dirtyPrefix = currentFile?.dirty ? '* ' : '';
  const title = currentFile ? `${dirtyPrefix}Edit: ${currentFile.path}` : 'Editor';
  useDocumentTitle(title);

  return (
    <Layout title={title} noPadding>
      <div className="flex h-full">
        <EditorSidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <Breadcrumb />
          <div className="flex-1 overflow-hidden">
            <EditorPageContent />
          </div>
        </div>
      </div>
    </Layout>
  );
}
