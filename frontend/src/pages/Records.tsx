import React, { useState, useEffect } from 'react';
import {
  Database,
  Search,
  Download,
  Code2,
  X,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { apiClient } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { ImportedRecord, DatasetSchema } from '../types';

export const Records: React.FC = () => {
  const { activeOrg } = useAuth();
  const [records, setRecords] = useState<ImportedRecord[]>([]);
  const [schemas, setSchemas] = useState<DatasetSchema[]>([]);
  const [selectedSchema, setSelectedSchema] = useState('');
  const [searchExternalId, setSearchExternalId] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  // JSON viewer modal
  const [selectedRecord, setSelectedRecord] = useState<ImportedRecord | null>(null);

  const fetchRecords = async () => {
    setIsLoading(true);
    try {
      const params: any = { page };
      if (selectedSchema) params.schema_id = selectedSchema;
      if (searchExternalId) params.external_id = searchExternalId;

      const res = await apiClient.get('/records/', { params });
      setRecords(res.data.results || res.data || []);
      setTotalCount(res.data.count || (res.data.results ? res.data.results.length : 0));
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (activeOrg) {
      apiClient.get('/schemas/').then((res) => {
        setSchemas(res.data.results || res.data || []);
      });
      fetchRecords();
    }
  }, [activeOrg, page, selectedSchema]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchRecords();
  };

  const handleExportCSV = async () => {
    setIsExporting(true);
    try {
      const res = await apiClient.get('/exports/records/', {
        responseType: 'blob',
        params: selectedSchema ? { schema_id: selectedSchema } : {},
      });

      // Trigger browser download
      const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `nexora_records_${activeOrg?.slug || 'export'}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to export records CSV');
    } finally {
      setIsExporting(false);
    }
  };

  const totalPages = Math.ceil(totalCount / 20) || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Records Explorer</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Immutable stored data items with SHA-256 integrity hashes and tenant partitioning.
          </p>
        </div>
        <button
          onClick={handleExportCSV}
          disabled={isExporting}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition shadow-lg shadow-emerald-600/20 disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          <span>{isExporting ? 'Exporting...' : 'Export Sanitized CSV'}</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row items-center gap-3">
        <form onSubmit={handleSearch} className="flex-1 w-full flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by External ID..."
              value={searchExternalId}
              onChange={(e) => setSearchExternalId(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>
          <button
            type="submit"
            className="px-3.5 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition"
          >
            Search
          </button>
        </form>

        <div className="w-full sm:w-64">
          <select
            value={selectedSchema}
            onChange={(e) => {
              setSelectedSchema(e.target.value);
              setPage(1);
            }}
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
          >
            <option value="">All Schemas</option>
            {schemas.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Records Table */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-3 text-xs text-slate-400">
          <div>
            Showing <span className="text-white font-mono">{records.length}</span> of{' '}
            <span className="text-white font-mono">{totalCount}</span> records
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>SHA-256 Verified</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">External ID</th>
                <th className="py-2.5 px-3">Schema</th>
                <th className="py-2.5 px-3">SHA-256 Hash</th>
                <th className="py-2.5 px-3">Payload Summary</th>
                <th className="py-2.5 px-3">Ingested At</th>
                <th className="py-2.5 px-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {records.map((rec) => (
                <tr key={rec.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3 text-brand-400 font-bold max-w-[130px] truncate">
                    {rec.external_id}
                  </td>
                  <td className="py-3 px-3 text-slate-300">{rec.schema_name || 'Schema'}</td>
                  <td className="py-3 px-3 text-slate-500 text-[11px] max-w-[110px] truncate">
                    {rec.record_hash}
                  </td>
                  <td className="py-3 px-3 text-slate-400 max-w-[200px] truncate">
                    {JSON.stringify(rec.payload)}
                  </td>
                  <td className="py-3 px-3 text-slate-500 text-[11px]">
                    {new Date(rec.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => setSelectedRecord(rec)}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs font-medium inline-flex items-center gap-1 transition"
                    >
                      <Code2 className="w-3.5 h-3.5" />
                      <span>JSON</span>
                    </button>
                  </td>
                </tr>
              ))}
              {records.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    No imported records match your query.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-800/80 text-xs">
          <span className="text-slate-400">
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* JSON Viewer Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-sm">
                  Record: {selectedRecord.external_id}
                </h3>
                <p className="text-[11px] text-slate-400 font-mono">
                  Hash: {selectedRecord.record_hash}
                </p>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4">
              <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto max-h-80">
                {JSON.stringify(selectedRecord.payload, null, 2)}
              </pre>
            </div>

            <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-950/40">
              <button
                onClick={() => setSelectedRecord(null)}
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
