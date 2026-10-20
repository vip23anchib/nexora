import React, { useState, useEffect } from 'react';
import {
  FileCode2,
  Plus,
  Play,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Layers,
  X,
  Code2,
} from 'lucide-react';
import { apiClient } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { DatasetSchema, DatasetField, FieldType } from '../types';

export const Schemas: React.FC = () => {
  const { activeOrg } = useAuth();
  const [schemas, setSchemas] = useState<DatasetSchema[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTestModal, setShowTestModal] = useState<DatasetSchema | null>(null);

  // Schema creation state
  const [schemaName, setSchemaName] = useState('');
  const [schemaDesc, setSchemaDesc] = useState('');
  const [fields, setFields] = useState<DatasetField[]>([
    { name: 'customer_id', field_type: 'string', is_required: true, is_unique: true, order: 0 },
    { name: 'email', field_type: 'email', is_required: true, is_unique: false, order: 1 },
    { name: 'amount', field_type: 'decimal', is_required: true, is_unique: false, order: 2 },
  ]);
  const [createError, setCreateError] = useState<string | null>(null);

  // Test sample state
  const [samplePayload, setSamplePayload] = useState('{\n  "customer_id": "CUST-999",\n  "email": "jane@example.com",\n  "amount": 250.75\n}');
  const [validationResult, setValidationResult] = useState<any | null>(null);
  const [testingSample, setTestingSample] = useState(false);

  const fetchSchemas = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.get('/schemas/');
      setSchemas(res.data.results || res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (activeOrg) {
      fetchSchemas();
    }
  }, [activeOrg]);

  const addField = () => {
    setFields([
      ...fields,
      {
        name: `field_${fields.length + 1}`,
        field_type: 'string',
        is_required: false,
        is_unique: false,
        order: fields.length,
      },
    ]);
  };

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  const updateField = (index: number, updates: Partial<DatasetField>) => {
    setFields(
      fields.map((f, i) => (i === index ? { ...f, ...updates } : f))
    );
  };

  const handleCreateSchema = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    try {
      await apiClient.post('/schemas/', {
        name: schemaName,
        description: schemaDesc,
        fields,
      });
      setShowCreateModal(false);
      setSchemaName('');
      setSchemaDesc('');
      fetchSchemas();
    } catch (err: any) {
      setCreateError(
        err.response?.data?.detail ||
          err.response?.data?.name?.[0] ||
          'Failed to create schema. Please verify rules.'
      );
    }
  };

  const handleTestSample = async () => {
    if (!showTestModal) return;
    setTestingSample(true);
    setValidationResult(null);
    try {
      const parsed = JSON.parse(samplePayload);
      const res = await apiClient.post(`/schemas/${showTestModal.id}/validate_sample/`, {
        sample_data: parsed,
      });
      setValidationResult(res.data);
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setValidationResult({ valid: false, errors: { json: ['Invalid JSON syntax'] } });
      } else {
        setValidationResult(
          err.response?.data || { valid: false, errors: { error: ['Validation failed'] } }
        );
      }
    } finally {
      setTestingSample(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Dataset Schemas & Validation</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Define typed contract schemas, validation bounds, uniqueness constraints, and versions.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition shadow-lg shadow-brand-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Schema Contract</span>
        </button>
      </div>

      {/* Schema Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {schemas.map((schema) => (
          <div
            key={schema.id}
            className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white text-base truncate">{schema.name}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-500/15 text-brand-400 border border-brand-500/20">
                  v{schema.version}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1.5 line-clamp-2">
                {schema.description || 'No description provided.'}
              </p>

              {/* Field chips */}
              <div className="mt-4 pt-3 border-t border-slate-800/80">
                <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>Fields ({schema.fields?.length || 0})</span>
                  <span className="text-emerald-400 font-sans">Active</span>
                </div>
                <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                  {schema.fields?.map((f) => (
                    <span
                      key={f.name}
                      className="px-2 py-1 rounded-md bg-slate-800/80 text-[11px] font-mono text-slate-300 border border-slate-700/60"
                    >
                      {f.name}:{' '}
                      <span className="text-sky-400 font-semibold">{f.field_type}</span>
                      {f.is_required && <span className="text-rose-400 ml-0.5">*</span>}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
              <span className="text-[10px] text-slate-500 font-mono">
                {new Date(schema.created_at).toLocaleDateString()}
              </span>
              <button
                onClick={() => {
                  setShowTestModal(schema);
                  setValidationResult(null);
                  // prefill template json
                  const sampleObj: Record<string, any> = {};
                  schema.fields?.forEach((f) => {
                    if (f.field_type === 'integer') sampleObj[f.name] = 100;
                    else if (f.field_type === 'decimal') sampleObj[f.name] = 49.99;
                    else if (f.field_type === 'boolean') sampleObj[f.name] = true;
                    else if (f.field_type === 'email') sampleObj[f.name] = 'user@example.com';
                    else if (f.field_type === 'date') sampleObj[f.name] = '2026-01-15';
                    else sampleObj[f.name] = `demo_${f.name}`;
                  });
                  setSamplePayload(JSON.stringify(sampleObj, null, 2));
                }}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-brand-400 text-xs font-medium transition"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Test Validator</span>
              </button>
            </div>
          </div>
        ))}

        {schemas.length === 0 && !isLoading && (
          <div className="col-span-full p-12 text-center rounded-xl bg-slate-900/40 border border-dashed border-slate-800 text-slate-500">
            <FileCode2 className="w-10 h-10 mx-auto text-slate-600 mb-3" />
            <p className="text-sm font-medium text-slate-400">No schemas found in this workspace.</p>
            <p className="text-xs text-slate-600 mt-1">
              Create your first schema contract or load the seeded demo data.
            </p>
          </div>
        )}
      </div>

      {/* Test Sample Modal */}
      {showTestModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-brand-400" />
                <span className="font-semibold text-white text-sm">
                  Test Validator: {showTestModal.name} (v{showTestModal.version})
                </span>
              </div>
              <button
                onClick={() => setShowTestModal(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-3">
              <div>
                <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
                  Sample JSON Payload
                </label>
                <textarea
                  rows={8}
                  value={samplePayload}
                  onChange={(e) => setSamplePayload(e.target.value)}
                  className="w-full font-mono text-xs p-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-brand-500"
                />
              </div>

              {validationResult && (
                <div
                  className={`p-3 rounded-lg border text-xs font-mono ${
                    validationResult.valid
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                      : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-bold mb-1">
                    {validationResult.valid ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : (
                      <AlertCircle className="w-4 h-4" />
                    )}
                    <span>
                      {validationResult.valid
                        ? 'Validation Passed: Contract Valid'
                        : 'Validation Failed'}
                    </span>
                  </div>
                  {validationResult.errors && (
                    <pre className="text-[11px] overflow-x-auto mt-1 p-2 bg-slate-950/80 rounded">
                      {JSON.stringify(validationResult.errors, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-950/40">
              <button
                onClick={() => setShowTestModal(null)}
                className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:bg-slate-800"
              >
                Close
              </button>
              <button
                onClick={handleTestSample}
                disabled={testingSample}
                className="px-4 py-1.5 rounded-lg text-xs bg-brand-500 hover:bg-brand-600 text-white font-medium flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{testingSample ? 'Validating...' : 'Run Validator'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Schema Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl my-8">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCode2 className="w-5 h-5 text-brand-400" />
                <h3 className="font-bold text-white text-base">Create Dataset Schema Contract</h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSchema}>
              <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
                {createError && (
                  <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{createError}</span>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                      Schema Name *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. transactions_feed"
                      value={schemaName}
                      onChange={(e) => setSchemaName(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-brand-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                      Description
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Core ledger transactions"
                      value={schemaDesc}
                      onChange={(e) => setSchemaDesc(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-brand-500"
                    />
                  </div>
                </div>

                {/* Fields Builder */}
                <div className="pt-2">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Dataset Fields ({fields.length})
                    </span>
                    <button
                      type="button"
                      onClick={addField}
                      className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 font-medium"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Field</span>
                    </button>
                  </div>

                  <div className="space-y-2">
                    {fields.map((field, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 flex flex-col sm:flex-row items-center gap-3"
                      >
                        <input
                          type="text"
                          required
                          value={field.name}
                          onChange={(e) => updateField(idx, { name: e.target.value })}
                          placeholder="field_name"
                          className="flex-1 px-2.5 py-1.5 bg-slate-900 border border-slate-800 rounded text-xs font-mono text-slate-200"
                        />
                        <select
                          value={field.field_type}
                          onChange={(e) =>
                            updateField(idx, { field_type: e.target.value as FieldType })
                          }
                          className="px-2.5 py-1.5 bg-slate-900 border border-slate-800 rounded text-xs font-mono text-slate-200"
                        >
                          <option value="string">string</option>
                          <option value="integer">integer</option>
                          <option value="decimal">decimal</option>
                          <option value="boolean">boolean</option>
                          <option value="date">date</option>
                          <option value="datetime">datetime</option>
                          <option value="email">email</option>
                        </select>
                        <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={field.is_required}
                            onChange={(e) => updateField(idx, { is_required: e.target.checked })}
                            className="rounded bg-slate-900 border-slate-700 text-brand-500"
                          />
                          <span>Required</span>
                        </label>
                        <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={field.is_unique}
                            onChange={(e) => updateField(idx, { is_unique: e.target.checked })}
                            className="rounded bg-slate-900 border-slate-700 text-brand-500"
                          />
                          <span>Unique</span>
                        </label>
                        {fields.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeField(idx)}
                            className="text-slate-500 hover:text-rose-400 p-1"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-950/60">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg text-xs bg-brand-500 hover:bg-brand-600 text-white font-medium"
                >
                  Create Schema
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
