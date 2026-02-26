/**
 * DashboardPage — fleet summary with stat cards, recent activity, and quick nav.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, Activity, Radio, Minus, ArrowRight, Settings, Clock } from 'lucide-react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/common/Card';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useAgents } from '@/hooks/useAgents';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useGatewayStore } from '@/stores/gatewayStore';
import { formatRelativeTime } from '@/utils/time';
import type { AgentSummary } from '@/types';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  valueClass?: string;
}

function StatCard({ label, value, icon, valueClass = 'text-text-primary' }: StatCardProps): React.ReactElement {
  return (
    <div className="bg-bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-text-secondary text-xs">{label}</p>
        <span className="text-text-secondary">{icon}</span>
      </div>
      <p className={`font-semibold text-2xl tabular-nums ${valueClass}`}>{value}</p>
    </div>
  );
}

interface DashboardStatsProps {
  agents: AgentSummary[];
}

function DashboardStats({ agents }: DashboardStatsProps): React.ReactElement {
  const gatewayStatus = useGatewayStore((s) => s.status);
  const activeCount = agents.filter((a) => a.status === 'active').length;
  const idleCount = agents.filter((a) => a.status === 'idle').length;

  const gatewayValue = gatewayStatus === null ? '…' : gatewayStatus.running ? 'On' : 'Off';
  const gatewayValueClass = gatewayStatus?.running ? 'text-success' : 'text-text-secondary';

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      <StatCard label="Total Agents" value={agents.length} icon={<Bot size={16} />} />
      <StatCard
        label="Active"
        value={activeCount}
        icon={<Activity size={16} />}
        valueClass={activeCount > 0 ? 'text-success' : 'text-text-secondary'}
      />
      <StatCard
        label="Gateway"
        value={gatewayValue}
        icon={<Radio size={16} />}
        valueClass={gatewayValueClass}
      />
      <StatCard
        label="Idle"
        value={idleCount}
        icon={<Minus size={16} />}
        valueClass={idleCount > 0 ? 'text-warning' : 'text-text-secondary'}
      />
    </div>
  );
}

function RecentActivity({ agents }: { agents: AgentSummary[] }): React.ReactElement {
  const navigate = useNavigate();

  // Sort by last_activity descending, take top 5
  const recent = [...agents]
    .filter((a) => a.last_activity)
    .sort((a, b) => {
      const aTime = a.last_activity ? new Date(a.last_activity).getTime() : 0;
      const bTime = b.last_activity ? new Date(b.last_activity).getTime() : 0;
      return bTime - aTime;
    })
    .slice(0, 5);

  if (recent.length === 0) {
    return (
      <p className="text-text-secondary text-sm py-4">No recent agent activity.</p>
    );
  }

  return (
    <div className="space-y-2">
      {recent.map((agent) => (
        <div
          key={agent.id}
          className="flex items-center justify-between bg-bg-card border border-border rounded-lg px-4 py-3 cursor-pointer hover:bg-bg-hover transition-colors"
          onClick={() => navigate(`/agents/${encodeURIComponent(agent.id)}`)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              navigate(`/agents/${encodeURIComponent(agent.id)}`);
            }
          }}
        >
          <div className="flex items-center gap-3">
            <span
              className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                agent.status === 'active' ? 'bg-success' : agent.status === 'idle' ? 'bg-warning' : 'bg-text-secondary'
              }`}
            />
            <div>
              <p className="text-text-primary text-sm font-medium">{agent.name}</p>
              <p className="text-text-secondary text-xs font-mono">{agent.id}</p>
            </div>
          </div>
          <span className="flex items-center gap-1 text-text-secondary text-xs">
            <Clock size={11} />
            {formatRelativeTime(agent.last_activity ?? null)}
          </span>
        </div>
      ))}
    </div>
  );
}

function GatewaySummary(): React.ReactElement {
  const gatewayStatus = useGatewayStore((s) => s.status);
  const navigate = useNavigate();

  const statusText = gatewayStatus === null
    ? 'Loading…'
    : gatewayStatus.running
    ? 'Running'
    : gatewayStatus.error
    ? 'Error'
    : 'Stopped';

  const statusClass = gatewayStatus === null
    ? 'text-text-secondary'
    : gatewayStatus.running
    ? 'text-success'
    : gatewayStatus.error
    ? 'text-danger'
    : 'text-text-secondary';

  return (
    <Card
      hoverable
      onClick={() => navigate('/gateway')}
      className="mb-6"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Radio size={18} className="text-text-secondary" />
          <div>
            <p className="text-text-primary text-sm font-medium">Gateway Status</p>
            <p className={`text-xs font-semibold ${statusClass}`}>{statusText}</p>
          </div>
        </div>
        <ArrowRight size={16} className="text-text-secondary" />
      </div>
    </Card>
  );
}

function QuickNav(): React.ReactElement {
  const navigate = useNavigate();

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <Card hoverable onClick={() => navigate('/agents')}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot size={18} className="text-accent" />
            <span className="text-text-primary text-sm font-medium">View All Agents</span>
          </div>
          <ArrowRight size={16} className="text-text-secondary" />
        </div>
      </Card>
      <Card hoverable onClick={() => navigate('/config')}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings size={18} className="text-accent" />
            <span className="text-text-primary text-sm font-medium">Open Config</span>
          </div>
          <ArrowRight size={16} className="text-text-secondary" />
        </div>
      </Card>
    </div>
  );
}

function DashboardContent(): React.ReactElement {
  const { agents } = useAgents();

  return (
    <>
      <DashboardStats agents={agents} />
      <GatewaySummary />

      <h2 className="text-text-primary font-semibold text-sm mb-3">
        Fleet ({agents.length})
      </h2>
      <div className="mb-6">
        <RecentActivity agents={agents} />
      </div>

      <QuickNav />
    </>
  );
}

export default function DashboardPage(): React.ReactElement {
  useDocumentTitle('Dashboard');

  return (
    <Layout title="Fleet Overview">
      <ErrorBoundary label="Dashboard error">
        <DashboardContent />
      </ErrorBoundary>
    </Layout>
  );
}
