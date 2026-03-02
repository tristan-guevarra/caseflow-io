'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import api from '@/lib/api';
import type { UserWithMemberships, Membership } from '@/types';

interface AuthState {
  user: UserWithMemberships | null;
  currentMembership: Membership | null;
  orgId: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, orgName: string) => Promise<void>;
  logout: () => void;
  switchOrg: (orgId: string) => void;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    currentMembership: null,
    orgId: null,
    isLoading: true,
    isAuthenticated: false,
  });

  // grab user info from the api
  const fetchUser = useCallback(async () => {
    try {
      const { data } = await api.get('/auth/me');
      const user = data as UserWithMemberships;
      const savedOrgId = Cookies.get('org_id');
      const membership = user.memberships.find(m => m.organization_id === savedOrgId) || user.memberships[0];
      const orgId = membership?.organization_id || null;

      if (orgId) Cookies.set('org_id', orgId, { expires: 30 });

      setState({
        user,
        currentMembership: membership || null,
        orgId,
        isLoading: false,
        isAuthenticated: true,
      });
    } catch {
      setState(prev => ({ ...prev, isLoading: false, isAuthenticated: false }));
    }
  }, []);

  // check for token on mount
  useEffect(() => {
    const token = Cookies.get('access_token');
    if (token) {
      fetchUser();
    } else {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [fetchUser]);

  // login and save tokens
  const login = async (email: string, password: string) => {
    const { data } = await api.post('/auth/login', { email, password });
    Cookies.set('access_token', data.access_token, { expires: 1 });
    Cookies.set('refresh_token', data.refresh_token, { expires: 7 });
    await fetchUser();
    router.push('/dashboard');
  };

  // register new account
  const register = async (email: string, password: string, fullName: string, orgName: string) => {
    const { data } = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      organization_name: orgName,
    });
    Cookies.set('access_token', data.access_token, { expires: 1 });
    Cookies.set('refresh_token', data.refresh_token, { expires: 7 });
    await fetchUser();
    router.push('/dashboard');
  };

  // clear everything and redirect to login
  const logout = () => {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    Cookies.remove('org_id');
    setState({ user: null, currentMembership: null, orgId: null, isLoading: false, isAuthenticated: false });
    router.push('/login');
  };

  // switch to a different org
  const switchOrg = (orgId: string) => {
    const membership = state.user?.memberships.find(m => m.organization_id === orgId);
    if (membership) {
      Cookies.set('org_id', orgId, { expires: 30 });
      setState(prev => ({ ...prev, orgId, currentMembership: membership }));
    }
  };

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, switchOrg, refetchUser: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
