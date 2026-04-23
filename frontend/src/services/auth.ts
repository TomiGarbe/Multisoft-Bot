import api from './api';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

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

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login', { email, password });
  setToken(data.access_token, data.refresh_token);
  return data;
}

export function logout(): void {
  removeToken();
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
}

export function removeToken(): void {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  clearCookie(ACCESS_TOKEN_KEY);
  clearCookie(REFRESH_TOKEN_KEY);
}
