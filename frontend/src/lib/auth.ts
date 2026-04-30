// Auth utilities for token management

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

const setCookie = (name: string, value: string): void => {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=86400; samesite=lax`;
};

const clearCookie = (name: string): void => {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=; path=/; max-age=0; samesite=lax`;
};

export const getAccessToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
};

export const getRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

export const setTokens = (accessToken: string, refreshToken: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  setCookie(ACCESS_TOKEN_KEY, accessToken);
  setCookie(REFRESH_TOKEN_KEY, refreshToken);
};

export const clearTokens = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  clearCookie(ACCESS_TOKEN_KEY);
  clearCookie(REFRESH_TOKEN_KEY);
};

export const isAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;
  return !!getAccessToken();
};
