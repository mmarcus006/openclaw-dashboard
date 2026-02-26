/**
 * ConfigEditor — Monaco editor for openclaw.json with auto-validation.
 * Also lazy-loaded via React.lazy() from ConfigPage.
 */

import React, { useEffect, useCallback, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import { Save, RefreshCw, CheckCircle, XCircle, FileJson } from 'lucide-react';
import { useConfigStore } from '@/stores/configStore';
import { useToastStore } from '@/stores/toastStore';
import { Button } from '@/components/common/Button';
import { Spinner } from '@/components/common/Spinner';
import { Modal } from '@/components/common/Modal';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';

const MONACO_OPTIONS = {
  fontSize: 13,
  fontFamily: '"JetBrains Mono", ui-monospace, monospace',
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  wordWrap: 'on' as const,
  tabSize: 2,
  automaticLayout: true,
  formatOnPaste: true,
  formatOnType: true,
} as const;

const VALIDATE_DEBOUNCE_MS = 500;

export function ConfigEditor(): React.ReactElement {
  const content = useConfigStore((s) => s.content);
  const dirty = useConfigStore((s) => s.dirty);
  const loading = useConfigStore((s) => s.loading);
  const saving = useConfigStore((s) => s.saving);
  const error = useConfigStore((s) => s.error);
  const validation = useConfigStore((s) => s.validation);
  const path = useConfigStore((s) => s.path);
  const fetchConfig = useConfigStore((s) => s.fetchConfig);
  const updateContent = useConfigStore((s) => s.updateContent);
  const saveConfig = useConfigStore((s) => s.saveConfig);
  const validateConfig = useConfigStore((s) => s.validateConfig);
  const clearConflict = useConfigStore((s) => s.clearConflict);
  const addToast = useToastStore((s) => s.addToast);
  const validateTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const [showReloadConfirm, setShowReloadConfirm] = useState(false);

  const handleSave = useCallback(async () => {
    const success = await saveConfig();
    if (success) {
      addToast('success', 'Config saved — backup created automatically');
    } else if (error !== 'CONFLICT') {
      addToast('error', `Save failed: ${error ?? 'Unknown error'}`);
    }
  }, [saveConfig, addToast, error]);

  const handleReload = useCallback(() => {
    if (dirty) {
      setShowReloadConfirm(true);
    } else {
      void fetchConfig();
    }
  }, [dirty, fetchConfig]);

  const confirmReload = useCallback(() => {
    setShowReloadConfirm(false);
    void fetchConfig();
  }, [fetchConfig]);

  // Auto-validate on content change (debounced)
  useEffect(() => {
    if (!content) return;
    clearTimeout(validateTimer.current);
    validateTimer.current = setTimeout(() => {
      void validateConfig();
    }, VALIDATE_DEBOUNCE_MS);
    return () => clearTimeout(validateTimer.current);
  }, [content, validateConfig]);

  // Cmd+S shortcut
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

  // beforeunload on dirty
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => { if (dirty) { e.preventDefault(); e.returnValue = ''; } };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [dirty]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="lg" label="Loading config…" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-bg-secondary flex-shrink-0 flex-wrap gap-2">
        <div className="flex items-center gap-3 min-w-0">
          <FileJson size={14} className="text-text-secondary flex-shrink-0" aria-hidden="true" />
          <span className="text-text-secondary text-xs font-mono truncate">{path}</span>
          {dirty && (
            <span
              className="w-2 h-2 rounded-full bg-warning flex-shrink-0"
              aria-label="Unsaved changes"
              title="Unsaved changes"
            />
          )}
          {/* Validation indicator */}
          {validation && (
            <span className="flex items-center gap-1 text-xs">
              {validation.valid ? (
                <>
                  <CheckCircle size={12} className="text-success" aria-hidden="true" />
                  <span className="text-success">Valid JSON</span>
                </>
              ) : (
                <>
                  <XCircle size={12} className="text-danger" aria-hidden="true" />
                  <span className="text-danger">{validation.errors?.[0] ?? 'Invalid'}</span>
                </>
              )}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReload}
          >
            <RefreshCw size={13} aria-hidden="true" />
            Reload
          </Button>
          <span title={!dirty ? 'No unsaved changes' : undefined}>
            <Button
              variant="primary"
              size="sm"
              loading={saving}
              disabled={!dirty}
              onClick={() => void handleSave()}
            >
              <Save size={13} aria-hidden="true" />
              Save
            </Button>
          </span>
        </div>
      </div>

      {/* Validation warnings */}
      {validation?.warnings && validation.warnings.length > 0 && (
        <div className="px-4 py-2 bg-warning/10 border-b border-warning/20 flex-shrink-0">
          {validation.warnings.map((w, i) => (
            <p key={i} className="text-warning text-xs">{w}</p>
          ))}
        </div>
      )}

      {/* Monaco Editor */}
      <div className="flex-1 overflow-hidden">
        <Editor
          height="100%"
          language="json"
          value={content}
          onChange={(val) => { if (val !== undefined) updateContent(val); }}
          theme="vs-dark"
          options={MONACO_OPTIONS}
          loading={<div className="flex items-center justify-center h-full"><Spinner size="lg" /></div>}
        />
      </div>

      {/* Reload confirm dialog */}
      <ConfirmDialog
        isOpen={showReloadConfirm}
        onConfirm={confirmReload}
        onCancel={() => setShowReloadConfirm(false)}
        title="Discard unsaved changes?"
        message="You have unsaved changes to openclaw.json. Reloading will discard them."
        confirmLabel="Discard & Reload"
        cancelLabel="Cancel"
        variant="warning"
      />

      {/* Conflict dialog */}
      {error === 'CONFLICT' && (
        <Modal
          isOpen
          onClose={clearConflict}
          title="Config changed externally"
          footer={
            <>
              <Button variant="secondary" size="sm" onClick={clearConflict}>
                Keep my changes
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => { clearConflict(); void fetchConfig(); }}
              >
                Reload from disk
              </Button>
            </>
          }
        >
          <p className="text-text-secondary text-sm">
            openclaw.json was modified externally since you loaded it. This usually happens when OpenClaw updates your config.
          </p>
        </Modal>
      )}
    </div>
  );
}
