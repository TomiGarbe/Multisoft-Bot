import axios, { AxiosInstance, AxiosError } from 'axios';
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getRefreshToken();
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          setTokens(response.data.access_token, response.data.refresh_token);

          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          return api(originalRequest);
        } else {
          clearTokens();
          window.location.href = '/login';
        }
      } catch {
        clearTokens();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
};

// Users API
export const usersApi = {
  getAll: (skip = 0, limit = 100) =>
    api.get('/auth/users', { params: { skip, limit } }),
  getById: (id: string) =>
    api.get(`/auth/users/${id}`),
  create: (data: { name: string; email: string; password: string; is_active?: boolean }) =>
    api.post('/auth/users', data),
  update: (id: string, data: any) =>
    api.put(`/auth/users/${id}`, data),
  delete: (id: string) =>
    api.delete(`/auth/users/${id}`),
};

// Roles API
export const rolesApi = {
  getAll: (skip = 0, limit = 100) =>
    api.get('/auth/roles', { params: { skip, limit } }),
  getById: (id: string) =>
    api.get(`/auth/roles/${id}`),
  create: (data: { name: string; description?: string }) =>
    api.post('/auth/roles', data),
  update: (id: string, data: any) =>
    api.put(`/auth/roles/${id}`, data),
  delete: (id: string) =>
    api.delete(`/auth/roles/${id}`),
};

// Permissions API
export const permissionsApi = {
  getAll: (skip = 0, limit = 100) =>
    api.get('/auth/permissions', { params: { skip, limit } }),
  getById: (id: string) =>
    api.get(`/auth/permissions/${id}`),
  create: (data: { code: string; name: string; description?: string }) =>
    api.post('/auth/permissions', data),
  update: (id: string, data: any) =>
    api.put(`/auth/permissions/${id}`, data),
  delete: (id: string) =>
    api.delete(`/auth/permissions/${id}`),
};
