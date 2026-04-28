import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import { getToken, login as loginService, logout as logoutService } from '@/services/auth';

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }

    setIsAuthenticated(true);
    setUser({
      id: 'placeholder',
      name: 'Admin User',
      email: 'admin@multisoft.local',
      role: 'admin',
    });
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        setError(null);
        setLoading(true);

        await loginService(email, password);
        setIsAuthenticated(true);
        setUser({
          id: 'placeholder',
          name: 'Admin User',
          email,
          role: 'admin',
        });

        router.replace('/dashboard');
      } catch (err: unknown) {
        const errorWithResponse = err as { response?: { data?: { detail?: string } } };
        const message =
          errorWithResponse.response?.data?.detail || 'No se pudo iniciar sesion';
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [router]
  );

  const logout = useCallback(() => {
    logoutService();
    setIsAuthenticated(false);
    setUser(null);
    router.replace('/login');
  }, [router]);

  return {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    logout,
  };
}
