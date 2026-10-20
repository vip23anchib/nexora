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
        setTrends(trendsRes.data.trends || []);
        setFailureDist(failRes.data.distribution || []);
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
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            COMPLETED
          </span>
        );
      case 'COMPLETED_WITH_ERRORS':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            PARTIAL (ERRORS)
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20 animate-pulse">
            PROCESSING
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            FAILED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-300">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">System Reliability Overview</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Real-time pipeline metrics and transaction throughput for{' '}
            <span className="text-slate-200 font-medium">{activeOrg?.name}</span>.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/ingestion"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition shadow-lg shadow-brand-500/20"
          >
            <UploadCloud className="w-4 h-4" />
            <span>New Ingestion</span>
          </Link>
          <Link
            to="/records"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Export CSV</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Records */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Records</span>
            <Database className="w-4 h-4 text-brand-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-white font-mono">
            {metrics?.total_records?.toLocaleString() ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-400 flex items-center gap-1">
            <span className="text-emerald-400 flex items-center">
              <TrendingUp className="w-3 h-3 mr-0.5" /> 100%
            </span>
            <span>tenant isolated</span>
          </div>
        </div>

        {/* Total Ingestion Jobs */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Jobs Orchestrated</span>
            <Layers className="w-4 h-4 text-sky-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-white font-mono">
            {metrics?.total_jobs?.toLocaleString() ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-400 flex items-center gap-1">
            <span>Active Schemas:</span>
            <span className="text-slate-200 font-semibold">{metrics?.active_schemas_count ?? 0}</span>
          </div>
        </div>

        {/* Success Rate */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Success Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-emerald-400 font-mono">
            {metrics?.success_rate_percent ?? 0}%
          </div>
          <div className="mt-1 text-xs text-slate-400 flex items-center gap-1">
            <span>State machine validated</span>
          </div>
        </div>

        {/* Row Errors */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Row Rejections</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-amber-400 font-mono">
            {metrics?.error_rows_count?.toLocaleString() ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-400 flex items-center gap-1">
            <span>Captured with exact line #</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ingestion Throughput Trends (2 cols) */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">Ingestion Trends & Throughput</h3>
              <p className="text-xs text-slate-400">7-day volume of valid rows vs rejected rows</p>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
              AGGREGATED DAILY
            </span>
          </div>

          <div className="h-64 w-full">
            {trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0EA5E9" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#0EA5E9" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#F43F5E" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="date" stroke="#64748B" fontSize={11} />
                  <YAxis stroke="#64748B" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      color: '#F8FAFC',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="successful_rows"
                    name="Valid Rows"
                    stroke="#0EA5E9"
                    fillOpacity={1}
                    fill="url(#colorSuccess)"
                  />
                  <Area
                    type="monotone"
                    dataKey="error_rows"
                    name="Rejected Rows"
                    stroke="#F43F5E"
                    fillOpacity={1}
                    fill="url(#colorErrors)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                Awaiting ingestion data to plot trends...
              </div>
            )}
          </div>
        </div>

        {/* Status Distribution Pie Chart (1 col) */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col">
          <div className="mb-4">
            <h3 className="font-semibold text-sm text-white">Job State Distribution</h3>
            <p className="text-xs text-slate-400">Workflow execution results</p>
          </div>

          <div className="h-48 w-full flex items-center justify-center">
            {failureDist.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={failureDist}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={70}
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
                      borderRadius: '8px',
                      color: '#F8FAFC',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-500">No jobs completed yet</div>
            )}
          </div>

          <div className="mt-auto space-y-1.5 pt-3 border-t border-slate-800 text-xs">
            {failureDist.map((item, idx) => (
              <div key={item.status} className="flex items-center justify-between text-slate-300">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                  />
                  <span>{item.status}</span>
                </div>
                <span className="font-mono text-slate-400">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Ingestion Jobs Table */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-sm text-white">Recent Pipeline Executions</h3>
            <p className="text-xs text-slate-400">Latest CSV batch ingestion workflows and status</p>
          </div>
          <Link
            to="/ingestion"
            className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 transition"
          >
            <span>View All Jobs</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">File / Target</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Rows Validated</th>
                <th className="py-2.5 px-3">Success / Errors</th>
                <th className="py-2.5 px-3">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {metrics?.recent_jobs && metrics.recent_jobs.length > 0 ? (
                metrics.recent_jobs.map((job: IngestionJob) => (
                  <tr key={job.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3">
                      <div className="font-medium text-slate-200">{job.file_name}</div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        Schema: {job.schema_name || job.schema}
                      </div>
                    </td>
                    <td className="py-3 px-3">{getStatusBadge(job.status)}</td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      {job.processed_rows} / {job.total_rows}
                    </td>
                    <td className="py-3 px-3 font-mono">
                      <span className="text-emerald-400">{job.successful_rows}</span>
                      <span className="text-slate-500"> / </span>
                      <span className={job.error_rows > 0 ? 'text-rose-400 font-bold' : 'text-slate-400'}>
                        {job.error_rows}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
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
