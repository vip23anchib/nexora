import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Database,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  ArrowUpRight,
  TrendingUp,
  Clock,
  Layers,
  FileSpreadsheet,
  Activity,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { apiClient } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { DashboardMetrics, IngestionJob } from '../types';

export const Dashboard: React.FC = () => {
  const { activeOrg } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [failureDist, setFailureDist] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!activeOrg) return;

    const loadDashboard = async () => {
      setIsLoading(true);
      try {
        const [dashRes, trendsRes, failRes] = await Promise.all([
          apiClient.get('/analytics/dashboard/'),
          apiClient.get('/analytics/ingestion-trends/?days=7'),
          apiClient.get('/analytics/failure-distribution/'),
        ]);

        setMetrics(dashRes.data);

        // Normalize trend items for chart
        const rawTrends = Array.isArray(trendsRes.data)
          ? trendsRes.data
          : trendsRes.data.trends || [];
        const normalizedTrends = rawTrends.map((t: any) => ({
          date: t.date?.substring(5) || t.date,
          successful_rows: t.successful_records ?? t.successful_rows ?? 0,
          error_rows: t.failed_records ?? t.error_rows ?? 0,
          jobs_count: t.jobs_count ?? 0,
        }));
        setTrends(normalizedTrends);

        // Normalize failure distribution
        const rawFails = Array.isArray(failRes.data)
          ? failRes.data
          : failRes.data.distribution || [];
        setFailureDist(rawFails);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboard();
  }, [activeOrg]);

  const COLORS = ['#0EA5E9', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  const getStatusBadge = (status: string) => {
    const s = status?.toLowerCase() || '';
    if (s === 'completed') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          COMPLETED
        </span>
      );
    }
    if (s === 'completed_with_errors') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/25">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          PARTIAL (ERRORS)
        </span>
      );
    }
    if (s === 'processing') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-sky-500/10 text-sky-400 border border-sky-500/25 animate-pulse">
          <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-ping" />
          PROCESSING
        </span>
      );
    }
    if (s === 'failed') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-rose-500/10 text-rose-400 border border-rose-500/25">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
          FAILED
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-mono bg-slate-800 text-slate-300">
        {status?.toUpperCase()}
      </span>
    );
  };

  // Derived rates
  const totalRecords = metrics?.total_records ?? 0;
  const failedRecords = metrics?.failed_records ?? metrics?.error_rows_count ?? 0;
  const successRate =
    metrics?.success_rate_percent ??
    (totalRecords > 0
      ? Math.max(0, 100 - (metrics?.validation_failure_rate ?? 0))
      : 100);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">System Reliability Overview</h1>
            <span className="px-2 py-0.5 text-[10px] font-mono uppercase rounded-full bg-brand-500/15 text-brand-400 border border-brand-500/25">
              Live Engine
            </span>
          </div>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Real-time pipeline metrics, transactional throughput, and data integrity for{' '}
            <span className="text-slate-200 font-semibold">{activeOrg?.name}</span>.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link
            to="/ingestion"
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-brand-500 to-sky-500 hover:from-brand-600 hover:to-sky-600 text-white text-xs font-semibold transition shadow-lg shadow-brand-500/20 active:scale-[0.98]"
          >
            <UploadCloud className="w-4 h-4" />
            <span>New Ingestion</span>
          </Link>
          <Link
            to="/records"
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-medium transition"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            <span>Records Explorer</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Records */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition shadow-lg group">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Total Ingested Records
            </span>
            <div className="w-8 h-8 rounded-lg bg-brand-500/10 text-brand-400 flex items-center justify-center border border-brand-500/20 group-hover:scale-110 transition">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white font-mono tracking-tight">
            {totalRecords.toLocaleString()}
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center justify-between">
            <span className="text-emerald-400 flex items-center font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-1" />
              100% Tenant Isolated
            </span>
            <span className="font-mono text-[11px] text-slate-500">SHA-256 Hashed</span>
          </div>
        </div>

        {/* Total Jobs */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition shadow-lg group">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Jobs Orchestrated
            </span>
            <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center border border-sky-500/20 group-hover:scale-110 transition">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white font-mono tracking-tight">
            {(metrics?.total_jobs ?? 0).toLocaleString()}
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center justify-between">
            <span>
              Active Schemas:{' '}
              <span className="text-slate-200 font-bold">{metrics?.active_schemas_count ?? 0}</span>
            </span>
            <span className="font-mono text-[11px] text-slate-500">Batch Chunked</span>
          </div>
        </div>

        {/* Pipeline Success Rate */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition shadow-lg group">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Pipeline Success Rate
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20 group-hover:scale-110 transition">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-emerald-400 font-mono tracking-tight">
            {successRate.toFixed(1)}%
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center justify-between">
            <span>State Machine Verified</span>
            <span className="text-emerald-400 font-mono text-[11px]">Strict Locks</span>
          </div>
        </div>

        {/* Row Errors */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition shadow-lg group">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Row Rejections
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20 group-hover:scale-110 transition">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-extrabold text-amber-400 font-mono tracking-tight">
            {failedRecords.toLocaleString()}
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center justify-between">
            <span>Granular Error Capture</span>
            <span className="font-mono text-[11px] text-amber-400">Row # Exact</span>
          </div>
        </div>
      </div>

      {/* Visualizations Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ingestion Throughput Trends (2 cols) */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-sm text-white">Ingestion Trends & Throughput</h3>
              <p className="text-xs text-slate-400">7-day volume of valid rows vs rejected rows</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-brand-500" />
                Valid Rows
              </span>
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                Rejected Rows
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            {trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0EA5E9" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#0EA5E9" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#F43F5E" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="date" stroke="#64748B" fontSize={11} />
                  <YAxis stroke="#64748B" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      borderColor: '#334155',
                      borderRadius: '12px',
                      color: '#F8FAFC',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="successful_rows"
                    name="Valid Rows"
                    stroke="#0EA5E9"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorSuccess)"
                  />
                  <Area
                    type="monotone"
                    dataKey="error_rows"
                    name="Rejected Rows"
                    stroke="#F43F5E"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorErrors)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-500">
                <Activity className="w-6 h-6 text-slate-600 mb-2 animate-pulse" />
                <span>Awaiting ingestion data to plot trends...</span>
              </div>
            )}
          </div>
        </div>

        {/* Error Breakdown (1 col) */}
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 shadow-lg flex flex-col">
          <div className="mb-4">
            <h3 className="font-bold text-sm text-white">Validation Error Breakdown</h3>
            <p className="text-xs text-slate-400">Systemic defect analysis by error code</p>
          </div>

          <div className="h-44 w-full flex items-center justify-center">
            {failureDist.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={failureDist}
                    dataKey="count"
                    nameKey="error_code"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={68}
                    paddingAngle={3}
                  >
                    {failureDist.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      borderColor: '#334155',
                      borderRadius: '10px',
                      color: '#F8FAFC',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-500 text-center">
                <ShieldCheck className="w-6 h-6 text-emerald-400 mx-auto mb-1 opacity-70" />
                <span>No active validation rejections recorded</span>
              </div>
            )}
          </div>

          <div className="mt-auto space-y-1.5 pt-3 border-t border-slate-800 text-xs">
            {failureDist.length > 0 ? (
              failureDist.slice(0, 4).map((item, idx) => (
                <div key={item.error_code} className="flex items-center justify-between text-slate-300">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                    />
                    <span className="font-mono text-[11px] truncate max-w-[140px]">
                      {item.error_code}
                    </span>
                  </div>
                  <span className="font-mono text-slate-400 font-semibold">{item.count}</span>
                </div>
              ))
            ) : (
              <div className="text-[11px] text-slate-500 text-center py-1">
                Zero data quality anomalies detected
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Pipeline Executions Table */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800/80 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-bold text-sm text-white">Recent Pipeline Executions</h3>
            <p className="text-xs text-slate-400">Latest CSV batch ingestion workflows and status</p>
          </div>
          <Link
            to="/ingestion"
            className="text-xs text-brand-400 hover:text-brand-300 font-semibold flex items-center gap-1 transition"
          >
            <span>Open Pipeline Queue</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">File / Target Schema</th>
                <th className="py-2.5 px-3">Workflow Status</th>
                <th className="py-2.5 px-3">Rows Validated</th>
                <th className="py-2.5 px-3">Valid / Rejected</th>
                <th className="py-2.5 px-3">Execution Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {metrics?.recent_jobs && metrics.recent_jobs.length > 0 ? (
                metrics.recent_jobs.map((job: IngestionJob) => {
                  const failed = job.failed_rows ?? job.error_rows ?? 0;
                  return (
                    <tr key={job.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-3">
                        <div className="font-semibold text-slate-200">{job.file_name}</div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Schema: {job.schema_name || 'Standard Dataset'}
                        </div>
                      </td>
                      <td className="py-3 px-3">{getStatusBadge(job.status)}</td>
                      <td className="py-3 px-3 font-mono text-slate-300">
                        {job.processed_rows} / {job.total_rows}
                      </td>
                      <td className="py-3 px-3 font-mono">
                        <span className="text-emerald-400 font-semibold">{job.successful_rows}</span>
                        <span className="text-slate-500"> / </span>
                        <span className={failed > 0 ? 'text-rose-400 font-bold' : 'text-slate-400'}>
                          {failed}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    No recent ingestion jobs found for this workspace.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
