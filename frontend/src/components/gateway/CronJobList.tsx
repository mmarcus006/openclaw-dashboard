/**
 * CronJobList — displays cron jobs from openclaw.json config.
 */

import React, { useEffect, useState } from 'react';
import { Timer } from 'lucide-react';
import cronstrue from 'cronstrue';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { EmptyState } from '@/components/common/EmptyState';
import { gatewayApi } from '@/api/gateway';
import type { CronJobEntry } from '@/types';

function humanSchedule(schedule: string): string {
  try {
    return cronstrue.toString(schedule, { use24HourTimeFormat: true });
  } catch {
    return schedule;
  }
}

export function CronJobList(): React.ReactElement {
  const [jobs, setJobs] = useState<CronJobEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      try {
        const { data } = await gatewayApi.cronJobs();
        if (!cancelled) setJobs(data.jobs);
      } catch {
        // non-critical
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <Card>
        <h4 className="text-text-secondary text-xs font-medium uppercase tracking-wide mb-3">
          Cron Jobs
        </h4>
        <div className="flex items-center gap-2 text-text-secondary text-sm py-4">
          <div className="w-3 h-3 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          Loading cron jobs…
        </div>
      </Card>
    );
  }

  if (jobs.length === 0) {
    return (
      <Card>
        <h4 className="text-text-secondary text-xs font-medium uppercase tracking-wide mb-3">
          Cron Jobs
        </h4>
        <EmptyState
          icon={<Timer size={32} />}
          title="No cron jobs"
          description="No cron jobs are configured in openclaw.json."
        />
      </Card>
    );
  }

  return (
    <Card>
      <h4 className="text-text-secondary text-xs font-medium uppercase tracking-wide mb-3">
        Cron Jobs
      </h4>
      <div className="overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-text-secondary text-xs uppercase tracking-wide">
              <th className="text-left py-2 pr-4 font-medium">Name</th>
              <th className="text-left py-2 pr-4 font-medium">Schedule</th>
              <th className="text-left py-2 pr-4 font-medium">Next Run</th>
              <th className="text-left py-2 font-medium">Enabled</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.name} className="border-b border-border/50">
                <td className="py-2 pr-4 text-text-primary font-mono text-xs">{job.name}</td>
                <td className="py-2 pr-4 text-text-secondary text-xs" title={job.schedule}>
                  {job.error ? (
                    <span className="text-danger">{job.error}</span>
                  ) : (
                    humanSchedule(job.schedule)
                  )}
                </td>
                <td className="py-2 pr-4 text-text-secondary text-xs">
                  {job.error ? (
                    <span className="text-danger">—</span>
                  ) : job.next_run ? (
                    new Date(job.next_run).toLocaleString()
                  ) : (
                    '—'
                  )}
                </td>
                <td className="py-2">
                  <Badge variant={job.enabled ? 'success' : 'neutral'}>
                    {job.enabled ? 'Yes' : 'No'}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
