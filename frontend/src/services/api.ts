import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window === 'undefined') {
    return config;
  }

  const token = localStorage.getItem('access_token');
  if (!token) {
    return config;
  }

  config.headers = config.headers ?? {};
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function getApiErrorMessage(error: unknown, fallback = 'Unexpected error'): string {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }

  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first?.msg === 'string') {
      return first.msg;
    }
  }

  return error.message || fallback;
}

export default api;
