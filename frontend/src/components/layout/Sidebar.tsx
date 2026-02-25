/**
 * Sidebar — navigation with keyboard support.
 */

import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, FileCode, Settings, Radio } from 'lucide-react';

interface NavItem {
  to: string;
  label: string;
  Icon: React.ElementType;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/agents', label: 'Agents', Icon: Bot },
  { to: '/editor', label: 'Editor', Icon: FileCode },
  { to: '/config', label: 'Config', Icon: Settings },
  { to: '/gateway', label: 'Gateway', Icon: Radio },
];

export function Sidebar(): React.ReactElement {
  return (
    <aside className="w-56 flex-shrink-0 bg-bg-secondary border-r border-border flex flex-col">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-xl" aria-hidden="true">🦞</span>
          <span className="font-semibold text-text-primary text-sm">OpenClaw</span>
        </div>
        <p className="text-text-secondary text-xs mt-0.5">Agent Dashboard</p>
      </div>

      {/* Navigation */}
      <nav aria-label="Main navigation" className="flex-1 px-2 py-4 space-y-1">
        {NAV_ITEMS.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `
              flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors
              focus:outline-none focus-visible:ring-2 focus-visible:ring-accent
              ${isActive
                ? 'bg-accent/15 text-accent'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
              }
            `}
          >
            <Icon size={16} aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border">
        <p className="text-text-secondary text-xs">v1.0.0</p>
      </div>
    </aside>
  );
}
