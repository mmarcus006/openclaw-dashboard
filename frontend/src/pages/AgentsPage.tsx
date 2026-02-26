/**
 * AgentsPage — searchable, filterable, sortable agent grid.
 */

import React, { useMemo } from 'react';
import { Layout } from '@/components/layout/Layout';
import { AgentGrid } from '@/components/agents/AgentGrid';
import { SearchInput } from '@/components/common/SearchInput';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useAgents } from '@/hooks/useAgents';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useAgentStore, filteredAgents } from '@/stores/agentStore';
import type { StatusFilter, SortField } from '@/stores/agentStore';

function AgentsContent(): React.ReactElement {
  const { loading, error } = useAgents();
  const allAgents = useAgentStore((s) => s.agents);
  const searchTerm = useAgentStore((s) => s.searchTerm);
  const statusFilter = useAgentStore((s) => s.statusFilter);
  const sortBy = useAgentStore((s) => s.sortBy);
  const setSearchTerm = useAgentStore((s) => s.setSearchTerm);
  const setStatusFilter = useAgentStore((s) => s.setStatusFilter);
  const setSortBy = useAgentStore((s) => s.setSortBy);

  const agents = useMemo(
    () => filteredAgents({ agents: allAgents, searchTerm, statusFilter, sortBy }),
    [allAgents, searchTerm, statusFilter, sortBy],
  );

  return (
    <>
      {/* Search and filter controls */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <SearchInput
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="Search agents by name, id, or model…"
          resultCount={searchTerm ? agents.length : undefined}
          className="flex-1"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          className="bg-bg-secondary border border-border rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          aria-label="Filter by status"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="idle">Idle</option>
          <option value="stopped">Stopped</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortField)}
          className="bg-bg-secondary border border-border rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          aria-label="Sort by"
        >
          <option value="name">Sort: Name</option>
          <option value="status">Sort: Status</option>
          <option value="last_activity">Sort: Last Activity</option>
        </select>
      </div>

      <AgentGrid agents={agents} loading={loading} error={error} />
    </>
  );
}

export default function AgentsPage(): React.ReactElement {
  useDocumentTitle('Agents');

  return (
    <Layout title="Agents">
      <ErrorBoundary label="Agents error">
        <AgentsContent />
      </ErrorBoundary>
    </Layout>
  );
}
