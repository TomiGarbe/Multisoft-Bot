import api from './api';
import { clearActiveTenantContext } from './api';
import type { User } from '@/types/access';
import type { Tenant } from '@/types/tenant';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
export const AUTH_SESSION_CHANGED_EVENT = 'auth-session-changed';

const setCookie = (name: string, value: string) => {
  if (typeof document === 'undefined') {
    return;
  }

  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=86400; samesite=lax`;
};

const clearCookie = (name: string) => {
  if (typeof document === 'undefined') {
    return;
  }

  document.cookie = `${name}=; path=/; max-age=0; samesite=lax`;
};

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

export interface AuthContextResponse {
  user: User;
  tenants: Tenant[];
  is_global_access: boolean;
}

function notifyAuthSessionChanged(reason: string): void {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(AUTH_SESSION_CHANGED_EVENT, { detail: { reason } }));
}

function clearLegacySessionStorage(): void {
  if (typeof window === 'undefined') return;
  const keysToRemove = ['user', 'currentUser', 'auth_user', 'auth_context_cache'];
  for (const key of keysToRemove) {
    window.localStorage.removeItem(key);
    window.sessionStorage.removeItem(key);
  }
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  // Session switch must start from a clean state.
  removeToken();
  clearActiveTenantContext();
  clearLegacySessionStorage();
  notifyAuthSessionChanged('login-start');
  const { data } = await api.post<LoginResponse>('/auth/login', { email, password });
  setToken(data.access_token, data.refresh_token);
  clearActiveTenantContext();
  notifyAuthSessionChanged('login-success');
  return data;
}

export function logout(): void {
  removeToken();
  clearLegacySessionStorage();
  clearActiveTenantContext();
  notifyAuthSessionChanged('logout');
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me');
  return data;
}

export async function getAuthContext(): Promise<AuthContextResponse> {
  const { data } = await api.get<AuthContextResponse>('/auth/context');
  return data;
}

export function getToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setToken(accessToken: string, refreshToken?: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  setCookie(ACCESS_TOKEN_KEY, accessToken);

  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    setCookie(REFRESH_TOKEN_KEY, refreshToken);
  }
  notifyAuthSessionChanged('token-set');
}

export function removeToken(): void {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  clearCookie(ACCESS_TOKEN_KEY);
  clearCookie(REFRESH_TOKEN_KEY);
  notifyAuthSessionChanged('token-removed');
}
