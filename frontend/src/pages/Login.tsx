import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Layers,
  Lock,
  Mail,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  Eye,
  EyeOff,
  Zap,
  CheckCircle2,
  Database,
  GitBranch,
} from 'lucide-react';

type Persona = 'admin' | 'operator' | 'analyst';

export const Login: React.FC = () => {
  const [selectedPersona, setSelectedPersona] = useState<Persona>('operator');
  const [email, setEmail] = useState('operator@nexora.io');
  const [password, setPassword] = useState('NexoraSecurePass123!');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSelectPersona = (persona: Persona) => {
    setSelectedPersona(persona);
    setError(null);
    if (persona === 'admin') {
      setEmail('admin@nexora.io');
      setPassword('NexoraSecurePass123!');
    } else if (persona === 'operator') {
      setEmail('operator@nexora.io');
      setPassword('NexoraSecurePass123!');
    } else {
      setEmail('analyst@nexora.io');
      setPassword('NexoraSecurePass123!');
    }
  };

  const handleQuickDemoLogin = async (persona: Persona) => {
    handleSelectPersona(persona);
    setError(null);
    setIsSubmitting(true);
    const creds = {
      admin: { email: 'admin@nexora.io', pass: 'NexoraSecurePass123!' },
      operator: { email: 'operator@nexora.io', pass: 'NexoraSecurePass123!' },
      analyst: { email: 'analyst@nexora.io', pass: 'NexoraSecurePass123!' },
    }[persona];

    try {
      await login(creds.email, creds.pass);
      navigate('/');
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          'Authentication failed. Please verify credentials.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          'Invalid email or password. Please verify your credentials.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070B18] text-slate-100 flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden selection:bg-brand-500 selection:text-white">
      {/* Dynamic ambient backdrop lighting */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-brand-500/15 via-sky-600/5 to-transparent rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-20 right-1/4 w-[450px] h-[450px] bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Decorative Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b12_1px,transparent_1px),linear-gradient(to_bottom,#1e293b12_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Header Branding */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="relative group mb-3">
            <div className="absolute -inset-1 bg-gradient-to-r from-brand-500 to-sky-400 rounded-2xl blur-md opacity-70 group-hover:opacity-100 transition duration-500" />
            <div className="relative w-14 h-14 rounded-2xl bg-[#0B132B] border border-brand-500/30 flex items-center justify-center shadow-2xl">
              <Layers className="w-7 h-7 text-brand-400" />
            </div>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            NEXORA <span className="text-brand-400 text-lg font-mono font-normal">v1.0</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-xs">
            Enterprise Multi-Tenant Data Processing & Reliability Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-900/80 backdrop-blur-2xl border border-slate-800/80 rounded-2xl p-7 shadow-[0_0_50px_-10px_rgba(14,165,233,0.12)]">
          {/* Persona Segmented Control */}
          <div className="mb-6">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold uppercase tracking-wider text-[11px] text-slate-300">
                Select Demo Persona
              </span>
              <span className="text-[11px] text-brand-400 font-mono">1-Click Sign In</span>
            </div>
            <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-950/80 rounded-xl border border-slate-800">
              {(['operator', 'admin', 'analyst'] as Persona[]).map((p) => {
                const isSelected = selectedPersona === p;
                const labelMap = {
                  operator: 'Operator',
                  admin: 'Org Admin',
                  analyst: 'Analyst',
                };
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => handleSelectPersona(p)}
                    className={`py-2 px-3 text-xs font-medium rounded-lg transition-all flex flex-col items-center justify-center ${
                      isSelected
                        ? 'bg-brand-500 text-white shadow-md shadow-brand-500/25 font-semibold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                    }`}
                  >
                    <span>{labelMap[p]}</span>
                  </button>
                );
              })}
            </div>
            <div className="mt-2 text-[11px] text-slate-400 text-center font-mono bg-slate-950/40 py-1 px-2 rounded border border-slate-800/50">
              {selectedPersona === 'operator' && 'Role: Can upload CSVs, execute pipelines & retry jobs.'}
              {selectedPersona === 'admin' && 'Role: Full organization administrative & team RBAC authority.'}
              {selectedPersona === 'analyst' && 'Role: Read-only analytics, record inspection & sanitized CSV export.'}
            </div>
          </div>

          {/* Error Message Banner */}
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-400 text-xs flex items-center gap-2.5 animate-fadeIn">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span className="leading-snug">{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative group">
                <Mail className="w-4 h-4 text-slate-500 group-focus-within:text-brand-400 absolute left-3.5 top-3 transition" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="name@company.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <span className="text-[11px] font-mono text-slate-500">Demo: NexoraSecurePass123!</span>
              </div>
              <div className="relative group">
                <Lock className="w-4 h-4 text-slate-500 group-focus-within:text-brand-400 absolute left-3.5 top-3 transition" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-slate-500 hover:text-slate-300 transition"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Primary Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-brand-500 to-sky-500 hover:from-brand-600 hover:to-sky-600 text-white font-semibold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-brand-500/25 disabled:opacity-60 cursor-pointer active:scale-[0.99]"
            >
              <span>{isSubmitting ? 'Authenticating Workspace...' : 'Sign In to Workspace'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            {/* Quick 1-Click Launch Button */}
            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleQuickDemoLogin(selectedPersona)}
              className="w-full py-2.5 px-4 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-brand-300 text-xs font-medium transition flex items-center justify-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>Instant 1-Click Launch as {selectedPersona.toUpperCase()}</span>
            </button>
          </form>

          {/* Enterprise Safeguards Footnote */}
          <div className="mt-6 pt-5 border-t border-slate-800 flex items-center justify-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Strict Tenant Isolation • Audit Stamped • JWT Protected</span>
          </div>
        </div>

        {/* Feature Pills */}
        <div className="grid grid-cols-3 gap-2 mt-6">
          <div className="p-2.5 rounded-xl bg-slate-900/40 border border-slate-800/60 text-center">
            <Database className="w-4 h-4 text-brand-400 mx-auto mb-1" />
            <div className="text-[11px] font-semibold text-slate-300">Chunked Engine</div>
            <div className="text-[10px] text-slate-500 font-mono">14k rows/sec</div>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-900/40 border border-slate-800/60 text-center">
            <GitBranch className="w-4 h-4 text-sky-400 mx-auto mb-1" />
            <div className="text-[11px] font-semibold text-slate-300">State Machine</div>
            <div className="text-[10px] text-slate-500 font-mono">Atomic Locks</div>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-900/40 border border-slate-800/60 text-center">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
            <div className="text-[11px] font-semibold text-slate-300">Deterministic</div>
            <div className="text-[10px] text-slate-500 font-mono">Idempotent</div>
          </div>
        </div>
      </div>
    </div>
  );
};
