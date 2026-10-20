import React, { useState, useEffect } from 'react';
import {
  Bell,
  Building2,
  ChevronDown,
  LogOut,
  User as UserIcon,
  CheckCircle2,
  AlertTriangle,
  Info,
  XCircle,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { apiClient } from '../../lib/api';
import { Notification } from '../../types';

export const TopBar: React.FC = () => {
  const { user, organizations, activeOrg, setActiveOrg, logout } = useAuth();
  const [showOrgMenu, setShowOrgMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = async () => {
    try {
      const res = await apiClient.get('/notifications/?limit=10');
      const items: Notification[] = res.data.results || res.data || [];
      setNotifications(items);
      setUnreadCount(items.filter((n) => !n.is_read).length);
    } catch (e) {
      // Ignore
    }
  };

  useEffect(() => {
    if (activeOrg) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 15000);
      return () => clearInterval(interval);
    }
  }, [activeOrg]);

  const markAllRead = async () => {
    try {
      await apiClient.post('/notifications/mark-all-read/');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (e) {
      // Ignore
    }
  };

  const markOneRead = async (id: string) => {
    try {
      await apiClient.post(`/notifications/${id}/mark-read/`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (e) {
      // Ignore
    }
  };

  return (
    <header className="h-16 bg-[#0B0F19]/90 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Workspace Selector */}
      <div className="relative">
        <button
          onClick={() => setShowOrgMenu(!showOrgMenu)}
          className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition text-sm text-slate-200"
        >
          <Building2 className="w-4 h-4 text-brand-400" />
          <span className="font-medium">{activeOrg?.name || 'Select Workspace'}</span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        </button>

        {showOrgMenu && (
          <div className="absolute left-0 mt-2 w-56 rounded-xl bg-slate-900 border border-slate-800 shadow-xl py-1 z-50">
            <div className="px-3 py-1.5 text-[11px] font-semibold uppercase text-slate-400 tracking-wider">
              Workspaces ({organizations.length})
            </div>
            {organizations.map((org) => (
              <button
                key={org.id}
                onClick={() => {
                  setActiveOrg(org);
                  setShowOrgMenu(false);
                }}
                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between transition ${
                  org.id === activeOrg?.id
                    ? 'bg-brand-500/10 text-brand-400 font-medium'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <span>{org.name}</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {org.role?.replace('_', ' ')}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right Controls: Notifications & User profile */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 relative transition"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-rose-500 text-[10px] font-bold text-white flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl z-50 overflow-hidden">
              <div className="p-3 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-slate-200">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-brand-500/20 text-brand-400 font-mono">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-xs text-brand-400 hover:text-brand-300 transition"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-72 overflow-y-auto divide-y divide-slate-800/60">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-sm text-slate-400">
                    No notifications yet.
                  </div>
                ) : (
                  notifications.map((n) => {
                    const iconMap = {
                      info: <Info className="w-4 h-4 text-sky-400" />,
                      success: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
                      warning: <AlertTriangle className="w-4 h-4 text-amber-400" />,
                      error: <XCircle className="w-4 h-4 text-rose-400" />,
                    };
                    return (
                      <div
                        key={n.id}
                        onClick={() => !n.is_read && markOneRead(n.id)}
                        className={`p-3 text-left transition cursor-pointer hover:bg-slate-800/50 flex gap-2.5 ${
                          !n.is_read ? 'bg-slate-850' : 'opacity-70'
                        }`}
                      >
                        <div className="shrink-0 mt-0.5">{iconMap[n.notification_type]}</div>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-semibold text-slate-200 truncate">
                            {n.title}
                          </div>
                          <div className="text-xs text-slate-400 line-clamp-2 mt-0.5">
                            {n.message}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono mt-1">
                            {new Date(n.created_at).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2.5 pl-2 pr-3 py-1 rounded-full bg-slate-900 border border-slate-800 hover:border-slate-700 transition"
          >
            <div className="w-7 h-7 rounded-full bg-brand-500/20 text-brand-400 flex items-center justify-center font-bold text-xs uppercase">
              {user?.first_name ? user.first_name[0] : user?.email ? user.email[0] : 'U'}
            </div>
            <span className="text-xs font-medium text-slate-200 truncate max-w-[120px]">
              {user?.email}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-52 rounded-xl bg-slate-900 border border-slate-800 shadow-xl py-1 z-50">
              <div className="px-3 py-2 border-b border-slate-800">
                <div className="text-xs font-semibold text-white">
                  {user?.first_name} {user?.last_name}
                </div>
                <div className="text-[11px] text-slate-400 truncate">{user?.email}</div>
              </div>
              <button
                onClick={() => {
                  setShowUserMenu(false);
                  logout();
                }}
                className="w-full text-left px-3 py-2 text-xs text-rose-400 hover:bg-rose-500/10 flex items-center gap-2 transition"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
