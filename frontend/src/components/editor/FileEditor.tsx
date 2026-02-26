/**
 * FileEditor — Monaco wrapper for single-file editing.
 * This file is imported via React.lazy() only — never at the top level.
 * Monaco is 2.5MB; lazy loading keeps non-editor pages fast.
 */

import React, { useEffect, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import type { Monaco } from '@monaco-editor/react';
import { Save } from 'lucide-react';
import { useEditorStore } from '@/stores/editorStore';
import { useToastStore } from '@/stores/toastStore';
import { Button } from '@/components/common/Button';
import { Spinner } from '@/components/common/Spinner';
import { Modal } from '@/components/common/Modal';
import { openclawDarkTheme, OPENCLAW_THEME_NAME } from '@/themes/monacoTheme';

const MONACO_OPTIONS = {
  fontSize: 13,
  fontFamily: '"JetBrains Mono", ui-monospace, monospace',
  fontLigatures: true,
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  lineNumbers: 'on' as const,
  renderWhitespace: 'selection' as const,
  wordWrap: 'on' as const,
  tabSize: 2,
  automaticLayout: true,
} as const;

export function FileEditor(): React.ReactElement | null {
  const currentFile = useEditorStore((s) => s.currentFile);
  const loading = useEditorStore((s) => s.loading);
  const saving = useEditorStore((s) => s.saving);
  const error = useEditorStore((s) => s.error);
  const updateContent = useEditorStore((s) => s.updateContent);
  const saveFile = useEditorStore((s) => s.saveFile);
  const loadFile = useEditorStore((s) => s.loadFile);
  const clearConflict = useEditorStore((s) => s.clearConflict);
  const keepMyChanges = useEditorStore((s) => s.keepMyChanges);
  const addToast = useToastStore((s) => s.addToast);

  const handleSave = useCallback(async () => {
    const success = await saveFile();
    if (success) {
      addToast('success', 'File saved');
    } else if (error !== 'CONFLICT') {
      addToast('error', `Save failed: ${error ?? 'Unknown error'}`);
    }
  }, [saveFile, addToast, error]);

  // Cmd+S / Ctrl+S keyboard shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        void handleSave();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleSave]);

  // beforeunload warning when dirty
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (currentFile?.dirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [currentFile?.dirty]);

  const handleReloadAfterConflict = async (): Promise<void> => {
    if (!currentFile) return;
    clearConflict();
    await loadFile(currentFile.agentId, currentFile.path);
  };

  const handleEditorWillMount = useCallback((monaco: Monaco) => {
    monaco.editor.defineTheme(OPENCLAW_THEME_NAME, openclawDarkTheme);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="lg" label="Loading file…" />
      </div>
    );
  }

  if (!currentFile) {
    return null;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-bg-secondary flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-text-secondary text-xs font-mono">
            {currentFile.agentId}
          </span>
          <span className="text-text-secondary text-xs">/</span>
          <span className="text-text-primary text-sm font-mono truncate">
            {currentFile.path}
          </span>
          {currentFile.dirty && (
            <span
              className="w-2 h-2 rounded-full bg-warning flex-shrink-0"
              aria-label="Unsaved changes"
              title="Unsaved changes"
            />
          )}
        </div>

        <span title={!currentFile.dirty ? 'No unsaved changes' : undefined}>
          <Button
            variant="primary"
            size="sm"
            loading={saving}
            disabled={!currentFile.dirty}
            onClick={() => void handleSave()}
          >
            <Save size={13} aria-hidden="true" />
            Save
          </Button>
        </span>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 overflow-hidden">
        <Editor
          height="100%"
          language={currentFile.language}
          value={currentFile.content}
          onChange={(val) => { if (val !== undefined) updateContent(val); }}
          theme={OPENCLAW_THEME_NAME}
          beforeMount={handleEditorWillMount}
          options={MONACO_OPTIONS}
          loading={<div className="flex items-center justify-center h-full"><Spinner size="lg" /></div>}
        />
      </div>

      {/* Conflict dialog */}
      {error === 'CONFLICT' && (
        <Modal
          isOpen
          onClose={clearConflict}
          title="File changed externally"
          footer={
            <>
              <Button variant="secondary" size="sm" onClick={keepMyChanges}>
                Keep my changes
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => void handleReloadAfterConflict()}
              >
                Reload from disk
              </Button>
            </>
          }
        >
          <p className="text-text-secondary text-sm">
            This file was modified externally (e.g., by a running agent) since you opened it.
          </p>
          <p className="text-text-secondary text-sm mt-2">
            <strong className="text-text-primary">Keep my changes</strong> — continue editing (force-save will overwrite the external changes).
          </p>
          <p className="text-text-secondary text-sm mt-1">
            <strong className="text-text-primary">Reload from disk</strong> — discard your changes and load the current version.
          </p>
        </Modal>
      )}
    </div>
  );
}
