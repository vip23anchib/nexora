import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileCode2,
  UploadCloud,
  Database,
  History,
  Users,
  Layers,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Schemas & Rules', href: '/schemas', icon: FileCode2 },
  { name: 'Ingestion Pipeline', href: '/ingestion', icon: UploadCloud },
  { name: 'Records Explorer', href: '/records', icon: Database },
  { name: 'Audit Trail', href: '/audit', icon: History },
  { name: 'Team & RBAC', href: '/team', icon: Users },
];

export const Sidebar: React.FC = () => {
  const { activeOrg } = useAuth();

  return (
    <aside className="w-64 bg-[#0B132B]/80 backdrop-blur-md border-r border-slate-800 flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-brand-600 to-sky-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
          <Layers className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-bold text-lg text-white tracking-tight">NEXORA</span>
          <span className="block text-[10px] font-mono tracking-wider text-brand-400 uppercase">
            Data Platform
          </span>
        </div>
      </div>

      {/* Organization Badge */}
      <div className="px-4 py-3 mx-3 my-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
        <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1">
          Active Workspace
        </div>
        <div className="font-medium text-sm text-slate-200 truncate">
          {activeOrg?.name || 'Default Workspace'}
        </div>
        <div className="flex items-center gap-1.5 mt-1.5">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-[11px] font-mono text-emerald-400 capitalize">
            Role: {activeOrg?.role?.replace('_', ' ') || 'Member'}
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.href}
              end={item.href === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30 font-semibold shadow-sm shadow-brand-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div className="p-4 border-t border-slate-800/80 text-xs text-slate-500 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          <span>Engine v1.0.0</span>
        </div>
        <span className="font-mono text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400">
          PROD-READY
        </span>
      </div>
    </aside>
  );
};
