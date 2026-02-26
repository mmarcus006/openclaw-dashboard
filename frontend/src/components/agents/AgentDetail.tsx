/**
 * AgentDetail — agent detail view with tabbed Files | Sessions.
 */

import React, { useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, FolderOpen, FileText, MessageSquare } from 'lucide-react';
import { getFileIcon } from '@/utils/fileIcons';
import { Badge, statusVariant } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { Spinner } from '@/components/common/Spinner';
import { SessionList } from '@/components/sessions/SessionList';
import { SessionViewer } from '@/components/sessions/SessionViewer';
import { useSessionStore } from '@/stores/sessionStore';
import type { AgentDetailResponse, AgentFileInfo } from '@/types';

interface AgentDetailProps {
  agent: AgentDetailResponse | null;
  loading: boolean;
  error: string | null;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function shortenModel(model: string): string {
  const parts = model.split('/');
  return parts[parts.length - 1] ?? model;
}

interface FileRowProps {
  file: AgentFileInfo;
  agentId: string;
}

function FileRow({ file, agentId }: FileRowProps): React.ReactElement {
  const navigate = useNavigate();

  const handleOpen = (): void => {
    void navigate(`/editor?agent=${encodeURIComponent(agentId)}&path=${encodeURIComponent(file.name)}`);
  };

  const Icon = getFileIcon(file.name);

  return (
    <tr
      className="border-b border-border hover:bg-bg-hover/40 cursor-pointer transition-colors focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-[-2px]"
      onClick={handleOpen}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleOpen(); } }}
      tabIndex={0}
      role="row"
      aria-label={`Open ${file.name}`}
    >
      <td className="py-2.5 px-4">
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-text-secondary flex-shrink-0" aria-hidden="true" />
          <span className="text-text-primary text-sm font-mono">{file.name}</span>
        </div>
      </td>
      <td className="py-2.5 px-4 text-text-secondary text-sm text-right">
        {formatBytes(file.size)}
      </td>
      <td className="py-2.5 px-4 text-text-secondary text-sm text-right">
        {formatDate(file.mtime)}
      </td>
    </tr>
  );
}

type TabId = 'files' | 'sessions';
const TABS: TabId[] = ['files', 'sessions'];

export function AgentDetail({ agent, loading, error }: AgentDetailProps): React.ReactElement {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab');
  const activeTab: TabId = tabParam === 'sessions' ? 'sessions' : 'files';
  const clearSessions = useSessionStore((s) => s.clearSessions);

  const setActiveTab = useCallback((tab: TabId) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (tab === 'files') { next.delete('tab'); } else { next.set('tab', tab); }
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  const handleTabKeyDown = useCallback((e: React.KeyboardEvent) => {
    const idx = TABS.indexOf(activeTab);
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      setActiveTab(TABS[(idx + 1) % TABS.length] as TabId);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      setActiveTab(TABS[(idx - 1 + TABS.length) % TABS.length] as TabId);
    }
  }, [activeTab, setActiveTab]);

  React.useEffect(() => {
    return () => clearSessions();
  }, [clearSessions]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" label="Loading agent..." />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
        <p className="text-danger text-sm">{error ?? 'Agent not found'}</p>
        <Button variant="secondary" size="sm" onClick={() => void navigate('/agents')}>
          Back to agents
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => void navigate('/agents')}
        className="mb-4"
      >
        <ArrowLeft size={14} aria-hidden="true" />
        Back to fleet
      </Button>

      {/* Agent header */}
      <Card className="mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-text-primary font-semibold text-lg">{agent.name}</h2>
              <Badge variant={statusVariant(agent.status)}>{agent.status}</Badge>
            </div>
            <p className="text-text-secondary text-sm font-mono mb-3">{agent.id}</p>
            <div className="flex items-center gap-2 text-text-secondary text-xs">
              <FolderOpen size={12} aria-hidden="true" />
              <span className="font-mono truncate max-w-xs" title={agent.workspace}>{agent.workspace}</span>
            </div>
          </div>
          <Badge variant="neutral">{shortenModel(agent.model)}</Badge>
        </div>
      </Card>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-border mb-0" role="tablist" aria-label="Agent detail tabs" onKeyDown={handleTabKeyDown}>
        <button
          role="tab"
          aria-selected={activeTab === 'files'}
          aria-controls="tabpanel-files"
          id="tab-files"
          tabIndex={activeTab === 'files' ? 0 : -1}
          onClick={() => setActiveTab('files')}
          className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'files'
              ? 'border-accent text-accent'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <FileText size={14} />
          Files ({(agent.files ?? []).length})
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'sessions'}
          aria-controls="tabpanel-sessions"
          id="tab-sessions"
          tabIndex={activeTab === 'sessions' ? 0 : -1}
          onClick={() => setActiveTab('sessions')}
          className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'sessions'
              ? 'border-accent text-accent'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <MessageSquare size={14} />
          Sessions
        </button>
      </div>

      {/* Tab content */}
      {activeTab === 'files' ? (
        <Card id="tabpanel-files" role="tabpanel" aria-labelledby="tab-files" className="p-0 overflow-hidden rounded-t-none border-t-0">
          {(agent.files ?? []).length === 0 ? (
            <div className="py-10 text-center">
              <p className="text-text-secondary text-sm">No files found in workspace</p>
            </div>
          ) : (
            <table className="w-full" role="grid" aria-label="Workspace files">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-2 px-4 text-left text-text-secondary text-xs font-medium uppercase tracking-wide">
                    Name
                  </th>
                  <th className="py-2 px-4 text-right text-text-secondary text-xs font-medium uppercase tracking-wide">
                    Size
                  </th>
                  <th className="py-2 px-4 text-right text-text-secondary text-xs font-medium uppercase tracking-wide">
                    Modified
                  </th>
                </tr>
              </thead>
              <tbody>
                {(agent.files ?? []).map((file) => (
                  <FileRow key={file.name} file={file} agentId={agent.id} />
                ))}
              </tbody>
            </table>
          )}
        </Card>
      ) : (
        <div id="tabpanel-sessions" role="tabpanel" aria-labelledby="tab-sessions" className="grid grid-cols-1 lg:grid-cols-[minmax(300px,380px)_1fr] gap-0 border border-border rounded-b-lg overflow-hidden bg-bg-card">
          {/* Session list */}
          <div className="border-r border-border max-h-[600px] overflow-y-auto">
            <SessionList agentId={agent.id} />
          </div>
          {/* Message viewer */}
          <div className="p-4 max-h-[600px] overflow-y-auto">
            <SessionViewer />
          </div>
        </div>
      )}
    </div>
  );
}
