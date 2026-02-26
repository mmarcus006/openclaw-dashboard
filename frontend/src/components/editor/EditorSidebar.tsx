/**
 * EditorSidebar — file browser sidebar for the editor.
 * Shows agent selector dropdown + recursive file list.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ChevronDown, ChevronRight, FolderOpen, PanelLeftClose, PanelLeft } from 'lucide-react';
import { useAgentStore } from '@/stores/agentStore';
import { useEditorStore } from '@/stores/editorStore';
import { agentsApi } from '@/api/agents';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { Spinner } from '@/components/common/Spinner';
import { getFileIcon } from '@/utils/fileIcons';
import type { FileEntry } from '@/types/files';

interface FileGroup {
  dir: string;
  files: FileEntry[];
}

function groupByDirectory(files: FileEntry[]): FileGroup[] {
  const groups = new Map<string, FileEntry[]>();
  for (const file of files) {
    const parts = file.path.split('/');
    const dir = parts.length > 1 ? parts.slice(0, -1).join('/') : '.';
    const existing = groups.get(dir);
    if (existing) {
      existing.push(file);
    } else {
      groups.set(dir, [file]);
    }
  }
  // Sort: root files first, then alphabetical dirs
  const sorted = [...groups.entries()].sort((a, b) => {
    if (a[0] === '.') return -1;
    if (b[0] === '.') return 1;
    return a[0].localeCompare(b[0]);
  });
  return sorted.map(([dir, files]) => ({ dir, files }));
}

export function EditorSidebar(): React.ReactElement {
  const [searchParams, setSearchParams] = useSearchParams();
  const agents = useAgentStore((s) => s.agents);
  const fetchAgents = useAgentStore((s) => s.fetchAgents);
  const currentFile = useEditorStore((s) => s.currentFile);
  const loadFile = useEditorStore((s) => s.loadFile);

  const selectedAgent = searchParams.get('agent') ?? '';
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [truncated, setTruncated] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [collapsedDirs, setCollapsedDirs] = useState<Set<string>>(new Set());

  // Confirm dialog state for dirty file switch
  const [pendingFile, setPendingFile] = useState<{ agentId: string; path: string } | null>(null);

  // Fetch agents on mount
  useEffect(() => {
    if (agents.length === 0) {
      void fetchAgents();
    }
  }, [agents.length, fetchAgents]);

  // Fetch files when agent changes
  useEffect(() => {
    if (!selectedAgent) return;
    setLoading(true);
    void agentsApi
      .listFiles(selectedAgent, { recursive: true, depth: 2, maxFiles: 200 })
      .then(({ data }) => {
        setFiles(data.files);
        setTruncated(data.truncated);
      })
      .catch(() => {
        setFiles([]);
      })
      .finally(() => setLoading(false));
  }, [selectedAgent]);

  const handleAgentChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const agentId = e.target.value;
      if (!agentId) return;
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('agent', agentId);
        next.delete('path');
        return next;
      });
    },
    [setSearchParams],
  );

  const openFile = useCallback(
    (agentId: string, path: string) => {
      // Check if current file is dirty
      if (currentFile?.dirty) {
        setPendingFile({ agentId, path });
        return;
      }
      setSearchParams({ agent: agentId, path });
      void loadFile(agentId, path);
    },
    [currentFile?.dirty, loadFile, setSearchParams],
  );

  const confirmSwitch = useCallback(() => {
    if (!pendingFile) return;
    setSearchParams({ agent: pendingFile.agentId, path: pendingFile.path });
    void loadFile(pendingFile.agentId, pendingFile.path);
    setPendingFile(null);
  }, [pendingFile, loadFile, setSearchParams]);

  const toggleDir = useCallback((dir: string) => {
    setCollapsedDirs((prev) => {
      const next = new Set(prev);
      if (next.has(dir)) {
        next.delete(dir);
      } else {
        next.add(dir);
      }
      return next;
    });
  }, []);

  if (collapsed) {
    return (
      <div className="flex flex-col items-center py-3 w-10 border-r border-border bg-bg-secondary flex-shrink-0">
        <button
          onClick={() => setCollapsed(false)}
          className="p-1.5 rounded hover:bg-bg-hover text-text-secondary hover:text-text-primary transition-colors"
          title="Expand sidebar"
        >
          <PanelLeft size={16} />
        </button>
      </div>
    );
  }

  const groups = groupByDirectory(files);

  return (
    <>
      <div className="flex flex-col w-60 border-r border-border bg-bg-secondary flex-shrink-0 overflow-hidden">
        {/* Header with collapse toggle */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-border">
          <span className="text-text-primary text-xs font-medium uppercase tracking-wider">Files</span>
          <button
            onClick={() => setCollapsed(true)}
            className="p-1 rounded hover:bg-bg-hover text-text-secondary hover:text-text-primary transition-colors"
            title="Collapse sidebar"
          >
            <PanelLeftClose size={14} />
          </button>
        </div>

        {/* Agent selector */}
        <div className="px-3 py-2 border-b border-border">
          <select
            value={selectedAgent}
            onChange={handleAgentChange}
            className="w-full bg-bg-primary border border-border rounded px-2 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent"
            aria-label="Select agent"
          >
            <option value="">Select agent...</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} ({a.id})
              </option>
            ))}
          </select>
        </div>

        {/* File list */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="sm" />
            </div>
          ) : !selectedAgent ? (
            <p className="text-text-tertiary text-xs text-center py-8">Select an agent to browse files</p>
          ) : files.length === 0 ? (
            <p className="text-text-tertiary text-xs text-center py-8">No files found</p>
          ) : (
            <>
              {groups.map((group) => (
                <div key={group.dir}>
                  {group.dir !== '.' && (
                    <button
                      onClick={() => toggleDir(group.dir)}
                      className="flex items-center gap-1.5 w-full px-3 py-1.5 text-xs text-text-secondary hover:bg-bg-hover transition-colors"
                    >
                      {collapsedDirs.has(group.dir) ? (
                        <ChevronRight size={12} />
                      ) : (
                        <ChevronDown size={12} />
                      )}
                      <FolderOpen size={12} />
                      <span className="truncate">{group.dir}</span>
                    </button>
                  )}
                  {!collapsedDirs.has(group.dir) &&
                    group.files.map((file) => {
                      const Icon = getFileIcon(file.name);
                      const isActive =
                        currentFile?.agentId === selectedAgent &&
                        currentFile?.path === file.path;
                      const isBinary = file.is_binary;

                      return (
                        <button
                          key={file.path}
                          onClick={() => {
                            if (!isBinary) openFile(selectedAgent, file.path);
                          }}
                          disabled={isBinary}
                          className={`flex items-center gap-2 w-full px-3 py-1 text-xs transition-colors ${
                            group.dir !== '.' ? 'pl-7' : ''
                          } ${
                            isActive
                              ? 'bg-accent/15 text-accent'
                              : isBinary
                              ? 'text-text-tertiary cursor-not-allowed opacity-60'
                              : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
                          }`}
                          title={isBinary ? 'Binary files cannot be edited' : file.path}
                        >
                          <Icon size={13} className="flex-shrink-0" />
                          <span className="truncate">{file.name}</span>
                        </button>
                      );
                    })}
                </div>
              ))}
              {truncated && (
                <p className="text-text-tertiary text-xs text-center py-2 italic">
                  File list truncated (200 max)
                </p>
              )}
            </>
          )}
        </div>
      </div>

      {/* Confirm dialog for dirty file switch */}
      <ConfirmDialog
        isOpen={pendingFile !== null}
        onConfirm={confirmSwitch}
        onCancel={() => setPendingFile(null)}
        title="Unsaved changes"
        message="You have unsaved changes. Switching files will discard them. Continue?"
        confirmLabel="Discard & switch"
        cancelLabel="Cancel"
        variant="warning"
      />
    </>
  );
}
