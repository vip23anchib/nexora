import React, { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  X,
} from 'lucide-react';
import { apiClient } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { OrganizationMembership, TenantRole } from '../types';

export const Team: React.FC = () => {
  const { activeOrg } = useAuth();
  const [members, setMembers] = useState<OrganizationMembership[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<TenantRole>('analyst');
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchMembers = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.get('/organizations/memberships/');
      setMembers(res.data.results || res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (activeOrg) {
      fetchMembers();
    }
  }, [activeOrg]);

  const handleRoleChange = async (membershipId: string, newRole: TenantRole) => {
    setMessage(null);
    try {
      await apiClient.patch(`/organizations/memberships/${membershipId}/`, {
        role: newRole,
      });
      setMessage({ text: 'Member role updated successfully', type: 'success' });
      fetchMembers();
    } catch (err: any) {
      setMessage({
        text:
          err.response?.data?.error ||
          err.response?.data?.detail ||
          'Failed to update role. Last admin protection may prevent this action.',
        type: 'error',
      });
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      await apiClient.post('/organizations/memberships/', {
        email: inviteEmail,
        role: inviteRole,
      });
      setMessage({ text: `Invited ${inviteEmail} as ${inviteRole}`, type: 'success' });
      setShowInviteModal(false);
      setInviteEmail('');
      fetchMembers();
    } catch (err: any) {
      setMessage({
        text:
          err.response?.data?.error ||
          err.response?.data?.detail ||
          'Failed to add member to organization.',
        type: 'error',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Team & Role-Based Access</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Manage organization collaborators, permissions, and tenant-scoped roles.
          </p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition shadow-lg shadow-brand-500/20"
        >
          <UserPlus className="w-4 h-4" />
          <span>Add Member</span>
        </button>
      </div>

      {/* Alert banner if role change succeeds or hits last admin safeguard */}
      {message && (
        <div
          className={`p-3.5 rounded-lg border text-xs flex items-center gap-2 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <ShieldAlert className="w-4 h-4 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Safeguards Card */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-400">
          <span className="font-semibold text-slate-200">Last Admin Safeguard:</span> The system
          enforces relational database constraints preventing the removal or demotion of an
          organization's sole administrator, ensuring your workspace cannot become orphaned.
        </div>
      </div>

      {/* Members Table */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Member</th>
                <th className="py-2.5 px-3">Role & Permissions</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Added</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {members.map((m) => (
                <tr key={m.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3">
                    <div className="font-semibold text-slate-200">
                      {m.user?.first_name} {m.user?.last_name || ''}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">{m.user?.email}</div>
                  </td>
                  <td className="py-3 px-3">
                    <select
                      value={m.role}
                      onChange={(e) => handleRoleChange(m.id, e.target.value as TenantRole)}
                      className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 focus:outline-none focus:border-brand-500 cursor-pointer"
                    >
                      <option value="org_admin">org_admin (Full Admin)</option>
                      <option value="operator">operator (Manage Ingestions)</option>
                      <option value="analyst">analyst (Read & Export)</option>
                      <option value="viewer">viewer (Read-only)</option>
                    </select>
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Active
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-500 font-mono text-[11px]">
                    {new Date(m.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {members.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-slate-500">
                    No team members found for this workspace.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-white text-sm">Add Team Member</h3>
              <button
                onClick={() => setShowInviteModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleInvite}>
              <div className="p-4 space-y-3">
                <div>
                  <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
                    User Email Address
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="teammate@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
                    Assign Role
                  </label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as TenantRole)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
                  >
                    <option value="org_admin">org_admin — Full workspace administrative power</option>
                    <option value="operator">operator — Upload and retry pipelines, modify schemas</option>
                    <option value="analyst">analyst — Query records, view metrics, export CSV</option>
                    <option value="viewer">viewer — Read-only observation</option>
                  </select>
                </div>
              </div>

              <div className="p-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-950/40">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg text-xs bg-brand-500 hover:bg-brand-600 text-white font-medium"
                >
                  Confirm Member
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
