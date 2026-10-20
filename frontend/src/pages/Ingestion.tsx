import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Layers,
  RotateCw,
  Eye,
  X,
  FileCheck2,
} from 'lucide-react';
import { apiClient } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { IngestionJob, DatasetSchema, DataSource, ImportRowError } from '../types';

export const Ingestion: React.FC = () => {
  const { activeOrg } = useAuth();
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [schemas, setSchemas] = useState<DatasetSchema[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Upload form state
  const [selectedSchema, setSelectedSchema] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [idempotencyKey, setIdempotencyKey] = useState(() => `idemp_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Job Inspector modal state
  const [inspectedJob, setInspectedJob] = useState<IngestionJob | null>(null);
  const [jobErrors, setJobErrors] = useState<ImportRowError[]>([]);
  const [workflowEvents, setWorkflowEvents] = useState<any[]>([]);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [jobsRes, schemasRes, sourcesRes] = await Promise.all([
        apiClient.get('/ingestion/jobs/'),
        apiClient.get('/schemas/'),
        apiClient.get('/data-sources/'),
      ]);
      setJobs(jobsRes.data.results || jobsRes.data || []);
      const scList = schemasRes.data.results || schemasRes.data || [];
      setSchemas(scList);
      if (scList.length > 0 && !selectedSchema) {
        setSelectedSchema(scList[0].id);
      }
      setDataSources(sourcesRes.data.results || sourcesRes.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (activeOrg) {
      fetchData();
      const interval = setInterval(() => {
        // poll active jobs
        apiClient.get('/ingestion/jobs/').then((res) => {
          setJobs(res.data.results || res.data || []);
        });
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [activeOrg]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !selectedSchema) {
      setUploadError('Please choose a file and target schema.');
      return;
    }

    setUploadError(null);
    setUploadSuccess(null);
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('schema_id', selectedSchema);
    if (selectedSource) {
      formData.append('data_source_id', selectedSource);
    }
    formData.append('idempotency_key', idempotencyKey);

    try {
      const res = await apiClient.post('/ingestion/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadSuccess(`Job created successfully: ${res.data.file_name} (${res.data.status})`);
      setFile(null);
      setIdempotencyKey(`idemp_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`);
      fetchData();
    } catch (err: any) {
      setUploadError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          'Failed to upload file. Check duplicate idempotency key or format.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const inspectJob = async (job: IngestionJob) => {
    setInspectedJob(job);
    setLoadingDetails(true);
    try {
      const [errorsRes, eventsRes] = await Promise.all([
        apiClient.get(`/ingestion/jobs/${job.id}/errors/`),
        apiClient.get(`/workflows/events/?job_id=${job.id}`),
      ]);
      setJobErrors(errorsRes.data.results || errorsRes.data || []);
      setWorkflowEvents(eventsRes.data.results || eventsRes.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleRetry = async (jobId: string) => {
    try {
      await apiClient.post(`/ingestion/jobs/${jobId}/retry/`);
      fetchData();
      if (inspectedJob && inspectedJob.id === jobId) {
        inspectJob({ ...inspectedJob, status: 'QUEUED' });
      }
    } catch (err: any) {
      alert(err.response?.data?.error || 'Retry failed');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">CSV Ingestion Pipeline</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Streaming chunked ingestion engine, idempotency validation, and deterministic row error capture.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Pipeline</span>
        </button>
      </div>

      {/* Upload Box */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-2 mb-4">
          <UploadCloud className="w-5 h-5 text-brand-400" />
          <h3 className="font-semibold text-white text-sm">Initiate Batch Ingestion</h3>
        </div>

        {uploadError && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {uploadSuccess && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{uploadSuccess}</span>
          </div>
        )}

        <form onSubmit={handleUpload} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Target Schema Contract *
            </label>
            <select
              value={selectedSchema}
              onChange={(e) => setSelectedSchema(e.target.value)}
              required
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
            >
              {schemas.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} (v{s.version}) — {s.fields?.length} fields
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Data Source (Optional)
            </label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
            >
              <option value="">None (Direct Ingestion)</option>
              {dataSources.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name} ({ds.source_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Idempotency Key *
              </label>
              <button
                type="button"
                onClick={() =>
                  setIdempotencyKey(`idemp_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`)
                }
                className="text-[10px] text-brand-400 hover:text-brand-300 font-mono"
              >
                Regenerate
              </button>
            </div>
            <input
              type="text"
              required
              value={idempotencyKey}
              onChange={(e) => setIdempotencyKey(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>

          {/* File Picker & Submit */}
          <div className="md:col-span-3 flex flex-col sm:flex-row items-center gap-4 pt-2">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
              className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
            />

            <button
              type="submit"
              disabled={isUploading || !file}
              className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white font-medium text-xs transition shadow-lg shadow-brand-500/20 whitespace-nowrap flex items-center justify-center gap-2"
            >
              <UploadCloud className="w-4 h-4" />
              <span>{isUploading ? 'Streaming & Parsing...' : 'Execute Ingestion Job'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Jobs Table */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
        <h3 className="font-semibold text-sm text-white mb-3">Ingestion Job Queue</h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">File / Schema</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Progress</th>
                <th className="py-2.5 px-3">Valid / Rejected</th>
                <th className="py-2.5 px-3">Idempotency Key</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3">
                    <div className="font-medium text-slate-200">{job.file_name}</div>
                    <div className="text-[11px] text-slate-500 font-mono">
                      {job.schema_name || 'Schema'}
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-mono ${
                        job.status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : job.status === 'COMPLETED_WITH_ERRORS'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : job.status === 'PROCESSING'
                          ? 'bg-sky-500/10 text-sky-400 animate-pulse border border-sky-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {job.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">
                    <div>
                      {job.processed_rows} / {job.total_rows} rows
                    </div>
                    <div className="w-24 bg-slate-800 rounded-full h-1.5 mt-1 overflow-hidden">
                      <div
                        className="bg-brand-500 h-1.5 rounded-full transition-all"
                        style={{
                          width: `${
                            job.total_rows > 0
                              ? Math.round((job.processed_rows / job.total_rows) * 100)
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono">
                    <span className="text-emerald-400 font-semibold">{job.successful_rows}</span>
                    <span className="text-slate-500"> / </span>
                    <span
                      className={
                        job.error_rows > 0 ? 'text-rose-400 font-bold' : 'text-slate-400'
                      }
                    >
                      {job.error_rows}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-400 max-w-[140px] truncate">
                    {job.idempotency_key}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => inspectJob(job)}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-brand-400 text-xs font-medium inline-flex items-center gap-1 transition"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No ingestion jobs recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Job Details / Errors Modal */}
      {inspectedJob && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl my-8">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-base">
                  Inspection: {inspectedJob.file_name}
                </h3>
                <p className="text-xs text-slate-400 font-mono">Job ID: {inspectedJob.id}</p>
              </div>
              <button
                onClick={() => setInspectedJob(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-5 max-h-[75vh] overflow-y-auto">
              {/* Summary Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-[10px] uppercase font-mono text-slate-400">Status</div>
                  <div className="text-sm font-bold text-white mt-0.5">{inspectedJob.status}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-[10px] uppercase font-mono text-slate-400">Total Rows</div>
                  <div className="text-sm font-bold text-white mt-0.5 font-mono">
                    {inspectedJob.total_rows}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-[10px] uppercase font-mono text-slate-400">Valid Rows</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5 font-mono">
                    {inspectedJob.successful_rows}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-[10px] uppercase font-mono text-slate-400">Row Errors</div>
                  <div className="text-sm font-bold text-rose-400 mt-0.5 font-mono">
                    {inspectedJob.error_rows}
                  </div>
                </div>
              </div>

              {/* Row-Level Errors Table */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 text-rose-400" />
                    <span>Row Validation Failures ({jobErrors.length})</span>
                  </h4>
                  {['FAILED', 'COMPLETED_WITH_ERRORS'].includes(inspectedJob.status) && (
                    <button
                      onClick={() => handleRetry(inspectedJob.id)}
                      className="flex items-center gap-1.5 px-3 py-1 rounded bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition"
                    >
                      <RotateCw className="w-3.5 h-3.5" />
                      <span>Safe Retry Job</span>
                    </button>
                  )}
                </div>

                {jobErrors.length > 0 ? (
                  <div className="border border-slate-800 rounded-lg overflow-x-auto max-h-56">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 sticky top-0">
                        <tr>
                          <th className="py-2 px-3">Row #</th>
                          <th className="py-2 px-3">Field</th>
                          <th className="py-2 px-3">Error Code</th>
                          <th className="py-2 px-3">Rejected Value</th>
                          <th className="py-2 px-3">Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {jobErrors.map((err) => (
                          <tr key={err.id} className="hover:bg-slate-800/40">
                            <td className="py-2 px-3 text-brand-400 font-bold">{err.row_number}</td>
                            <td className="py-2 px-3 text-slate-200">{err.field_name}</td>
                            <td className="py-2 px-3 text-amber-400">{err.error_code}</td>
                            <td className="py-2 px-3 text-rose-400 bg-rose-500/5 max-w-[120px] truncate">
                              {err.raw_value || 'null'}
                            </td>
                            <td className="py-2 px-3 text-slate-300 font-sans text-[11px]">
                              {err.error_message}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 text-center text-xs text-slate-500">
                    No row-level errors for this job. All rows were ingested cleanly!
                  </div>
                )}
              </div>

              {/* State Machine Transition Events */}
              <div>
                <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-sky-400" />
                  <span>Workflow State Machine Transitions ({workflowEvents.length})</span>
                </h4>
                <div className="space-y-1.5">
                  {workflowEvents.map((ev) => (
                    <div
                      key={ev.id}
                      className="p-2.5 rounded bg-slate-950/80 border border-slate-800/80 flex items-center justify-between text-xs font-mono"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400">{ev.from_state}</span>
                        <span className="text-brand-400">→</span>
                        <span className="text-emerald-400 font-bold">{ev.to_state}</span>
                        {ev.message && (
                          <span className="text-slate-400 font-sans text-[11px] ml-2">
                            ({ev.message})
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500">
                        {new Date(ev.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-950/40">
              <button
                onClick={() => setInspectedJob(null)}
                className="px-4 py-1.5 rounded-lg text-xs bg-slate-800 hover:bg-slate-700 text-slate-200"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
