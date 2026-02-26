/**
 * AgentDetail — agent detail view with flat file list.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, FolderOpen } from 'lucide-react';
import { getFileIcon } from '@/utils/fileIcons';
import { Badge, statusVariant } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { Spinner } from '@/components/common/Spinner';
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

export function AgentDetail({ agent, loading, error }: AgentDetailProps): React.ReactElement {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" label="Loading agent…" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
        <p className="text-danger text-sm">{error ?? 'Agent not found'}</p>
        <Button variant="secondary" size="sm" onClick={() => void navigate('/')}>
          Back to dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => void navigate('/')}
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

      {/* File list */}
      <Card className="p-0 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h3 className="text-text-primary font-medium text-sm">
            Workspace Files ({(agent.files ?? []).length})
          </h3>
        </div>

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
    </div>
  );
}
