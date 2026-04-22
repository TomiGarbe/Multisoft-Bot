'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/services/api';
import { setTokens, clearTokens, isAuthenticated, getAccessToken } from '@/lib/auth';

export interface User {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAccessToken();
      if (token) {
        // In a real app, you'd validate the token with the server
        setUser({ id: '', name: '', email: '', is_active: true });
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      setError(null);
      setLoading(true);

      const response = await authApi.login(email, password);

      setTokens(response.data.access_token, response.data.refresh_token);
      setUser({ id: '', name: '', email, is_active: true });

      router.push('/dashboard');
      return true;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [router]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    router.push('/login');
  }, [router]);

  return {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    logout,
  };
}
