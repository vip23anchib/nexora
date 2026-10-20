import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../lib/api';
import { User, Organization } from '../types';

interface AuthContextType {
  user: User | null;
  organizations: Organization[];
  activeOrg: Organization | null;
  setActiveOrg: (org: Organization) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUserProfile: () => Promise<void>;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [activeOrg, setActiveOrgState] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const setActiveOrg = (org: Organization) => {
    setActiveOrgState(org);
    localStorage.setItem('nexora_selected_org_id', org.id);
  };

  const refreshUserProfile = async () => {
    try {
      const meRes = await apiClient.get('/auth/me/');
      setUser(meRes.data.user);
      const orgs: Organization[] = meRes.data.organizations || [];
      setOrganizations(orgs);

      const savedOrgId = localStorage.getItem('nexora_selected_org_id');
      const matchedOrg = orgs.find((o) => o.id === savedOrgId) || orgs[0] || null;
      if (matchedOrg) {
        setActiveOrgState(matchedOrg);
        localStorage.setItem('nexora_selected_org_id', matchedOrg.id);
      }
    } catch (err) {
      setUser(null);
      setOrganizations([]);
      setActiveOrgState(null);
      localStorage.removeItem('nexora_access_token');
      localStorage.removeItem('nexora_refresh_token');
      localStorage.removeItem('nexora_selected_org_id');
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('nexora_access_token');
    if (token) {
      refreshUserProfile().finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const res = await apiClient.post('/auth/login/', { email, password });
    localStorage.setItem('nexora_access_token', res.data.access);
    localStorage.setItem('nexora_refresh_token', res.data.refresh);

    setUser(res.data.user);
    const orgs = res.data.organizations || [];
    setOrganizations(orgs);

    if (orgs.length > 0) {
      setActiveOrgState(orgs[0]);
      localStorage.setItem('nexora_selected_org_id', orgs[0].id);
    }
  };

  const logout = async () => {
    const refresh = localStorage.getItem('nexora_refresh_token');
    try {
      if (refresh) {
        await apiClient.post('/auth/logout/', { refresh });
      }
    } catch (e) {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('nexora_access_token');
      localStorage.removeItem('nexora_refresh_token');
      localStorage.removeItem('nexora_selected_org_id');
      setUser(null);
      setOrganizations([]);
      setActiveOrgState(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organizations,
        activeOrg,
        setActiveOrg,
        login,
        logout,
        refreshUserProfile,
        isLoading,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
