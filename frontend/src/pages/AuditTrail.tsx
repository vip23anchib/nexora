import React, { useState, useEffect } from 'react';
import { History, Shield, Search, RefreshCw, Code2, X } from 'lucide-react';
import { apiClient } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { AuditLog } from '../types';

export const AuditTrail: React.FC = () => {
  const { activeOrg } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [actionFilter, setActionFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [inspectedLog, setInspectedLog] = useState<AuditLog | null>(null);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const params: any = {};
      if (actionFilter) params.action = actionFilter;
      const res = await apiClient.get('/audit/', { params });
      setLogs(res.data.results || res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (activeOrg) {
      fetchLogs();
    }
  }, [activeOrg, actionFilter]);

  const getActionColor = (action: string) => {
    if (action.includes('LOGIN')) return 'text-sky-400 bg-sky-500/10 border-sky-500/20';
    if (action.includes('CREATE') || action.includes('UPLOAD'))
      return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (action.includes('UPDATE') || action.includes('RETRY'))
      return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Immutable Audit Trail</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Cryptographically stamped append-only event log with automatic sensitive data redaction.
          </p>
        </div>
        <button
          onClick={fetchLogs}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Audit</span>
        </button>
      </div>

      {/* Filter */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 uppercase font-mono tracking-wider">Action Filter:</span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
          >
            <option value="">All Actions</option>
            <option value="USER_LOGIN">USER_LOGIN</option>
            <option value="CSV_UPLOADED">CSV_UPLOADED</option>
            <option value="SCHEMA_CREATED">SCHEMA_CREATED</option>
            <option value="JOB_RETRIED">JOB_RETRIED</option>
            <option value="CSV_EXPORTED">CSV_EXPORTED</option>
            <option value="MEMBERSHIP_ROLE_UPDATED">MEMBERSHIP_ROLE_UPDATED</option>
          </select>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono">
          <Shield className="w-4 h-4" />
          <span>Append-Only Retention Active</span>
        </div>
      </div>

      {/* Logs Table */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Actor</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Resource Target</th>
                <th className="py-2.5 px-3">IP Address</th>
                <th className="py-2.5 px-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3 text-slate-400 text-[11px]">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-3 text-slate-200 font-bold max-w-[150px] truncate">
                    {log.actor_email}
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getActionColor(
                        log.action
                      )}`}
                    >
                      {log.action}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-300">
                    <span className="text-brand-400">{log.resource_type}</span>
                    <span className="text-slate-500 ml-1">({log.resource_id.substring(0, 8)}...)</span>
                  </td>
                  <td className="py-3 px-3 text-slate-500 text-[11px]">{log.ip_address}</td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => setInspectedLog(log)}
                      className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs inline-flex items-center gap-1 transition"
                    >
                      <Code2 className="w-3.5 h-3.5" />
                      <span>Payload</span>
                    </button>
                  </td>
                </tr>
              ))}
              {logs.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    No audit log records recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details modal */}
      {inspectedLog && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-sm">
                  Audit Entry: {inspectedLog.action}
                </h3>
                <p className="text-[11px] text-slate-400 font-mono">
                  Actor: {inspectedLog.actor_email}
                </p>
              </div>
              <button
                onClick={() => setInspectedLog(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4">
              <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-brand-300 overflow-x-auto max-h-80">
                {JSON.stringify(inspectedLog.details, null, 2)}
              </pre>
            </div>

            <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-950/40">
              <button
                onClick={() => setInspectedLog(null)}
                className="px-4 py-1.5 rounded-lg text-xs bg-slate-800 hover:bg-slate-700 text-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
