import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const ACTIVE_TENANT_ID_KEY = 'active_tenant_id';
const ACTIVE_SCOPE_KEY = 'active_scope';
export const TENANT_CONTEXT_CHANGED_EVENT = 'tenant-context-changed';

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
  const activeTenantId = localStorage.getItem(ACTIVE_TENANT_ID_KEY);
  const activeScope = (localStorage.getItem(ACTIVE_SCOPE_KEY) || 'tenant').trim().toLowerCase();
  if (!token) {
    return config;
  }

  config.headers = config.headers ?? {};
  config.headers.Authorization = `Bearer ${token}`;
  if (activeScope !== 'global' && activeTenantId && activeTenantId.trim().length > 0) {
    config.headers['X-Tenant-Id'] = activeTenantId;
  } else {
    delete (config.headers as Record<string, string>)['X-Tenant-Id'];
  }
  return config;
});

export type ActiveScope = 'tenant' | 'global';

function notifyTenantContextChanged(): void {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(TENANT_CONTEXT_CHANGED_EVENT));
}

export function setActiveTenantContext(tenantId: string | null, scope: ActiveScope = 'tenant'): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACTIVE_SCOPE_KEY, scope);
  if (tenantId && tenantId.trim().length > 0) {
    localStorage.setItem(ACTIVE_TENANT_ID_KEY, tenantId);
  } else {
    localStorage.removeItem(ACTIVE_TENANT_ID_KEY);
  }
  notifyTenantContextChanged();
}

export function clearActiveTenantContext(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACTIVE_SCOPE_KEY);
  localStorage.removeItem(ACTIVE_TENANT_ID_KEY);
  notifyTenantContextChanged();
}

export function getActiveTenantContext(): { tenantId: string | null; scope: ActiveScope } {
  if (typeof window === 'undefined') {
    return { tenantId: null, scope: 'tenant' };
  }
  const tenantId = localStorage.getItem(ACTIVE_TENANT_ID_KEY);
  const storedScope = (localStorage.getItem(ACTIVE_SCOPE_KEY) || 'tenant').trim().toLowerCase();
  return { tenantId, scope: storedScope === 'global' ? 'global' : 'tenant' };
}

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
