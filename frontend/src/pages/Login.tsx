import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Layers, Lock, Mail, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('admin@nexora.io');
  const [password, setPassword] = useState('NexoraSecurePass123!');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

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

  const setDemoCredentials = (role: 'admin' | 'operator' | 'analyst') => {
    if (role === 'admin') {
      setEmail('admin@nexora.io');
      setPassword('NexoraSecurePass123!');
    } else if (role === 'operator') {
      setEmail('operator@nexora.io');
      setPassword('NexoraSecurePass123!');
    } else {
      setEmail('analyst@nexora.io');
      setPassword('NexoraSecurePass123!');
    }
  };

  return (
    <div className="min-h-screen bg-[#070C1D] flex flex-col justify-center items-center px-4 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-brand-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-600 to-sky-400 flex items-center justify-center shadow-xl shadow-brand-500/25 mb-4">
            <Layers className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Nexora Enterprise</h1>
          <p className="text-sm text-slate-400 mt-1">Data Processing & Reliability Platform</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-8 shadow-2xl">
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="name@company.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-2.5 px-4 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm transition flex items-center justify-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50"
            >
              <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Workspace'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Fill Buttons */}
          <div className="mt-6 pt-6 border-t border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-2">
              <ShieldCheck className="w-3.5 h-3.5 text-brand-400" />
              <span>Fill Seeded Demo Personas:</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setDemoCredentials('admin')}
                className="px-2 py-1.5 text-xs rounded-md bg-slate-800/80 hover:bg-slate-800 text-slate-300 font-medium transition text-center"
              >
                Org Admin
              </button>
              <button
                type="button"
                onClick={() => setDemoCredentials('operator')}
                className="px-2 py-1.5 text-xs rounded-md bg-slate-800/80 hover:bg-slate-800 text-slate-300 font-medium transition text-center"
              >
                Operator
              </button>
              <button
                type="button"
                onClick={() => setDemoCredentials('analyst')}
                className="px-2 py-1.5 text-xs rounded-md bg-slate-800/80 hover:bg-slate-800 text-slate-300 font-medium transition text-center"
              >
                Analyst
              </button>
            </div>
          </div>
        </div>

        <div className="text-center mt-6 text-xs text-slate-600 font-mono">
          Nexora Reliability Platform • Multi-Tenant RBAC Enabled
        </div>
      </div>
    </div>
  );
};
