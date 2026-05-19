import axios from 'axios';

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.trim() ||
  (process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api/v1'
    : 'https://chatbotapi.multisoft.ar/api/v1');
const ACTIVE_TENANT_ID_KEY = 'active_tenant_id';
const LAST_SELECTED_TENANT_ID_KEY = 'last_selected_tenant_id';
export const TENANT_CONTEXT_CHANGED_EVENT = 'tenant-context-changed';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const isFormDataPayload = typeof FormData !== 'undefined' && config.data instanceof FormData;
  if (isFormDataPayload && config.headers) {
    delete (config.headers as Record<string, string>)['Content-Type'];
  }

  if (typeof window === 'undefined') {
    return config;
  }

  const token = localStorage.getItem('access_token');
  const activeTenantId = localStorage.getItem(ACTIVE_TENANT_ID_KEY);
  if (!token) {
    return config;
  }

  config.headers = config.headers ?? {};
  config.headers.Authorization = `Bearer ${token}`;
  if (activeTenantId && activeTenantId.trim().length > 0) {
    config.headers['X-Tenant-Id'] = activeTenantId;
  } else {
    delete (config.headers as Record<string, string>)['X-Tenant-Id'];
  }
  return config;
});

function notifyTenantContextChanged(): void {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(TENANT_CONTEXT_CHANGED_EVENT));
}

export function setActiveTenantContext(tenantId: string | null): void {
  if (typeof window === 'undefined') return;
  if (tenantId && tenantId.trim().length > 0) {
    localStorage.setItem(ACTIVE_TENANT_ID_KEY, tenantId);
    localStorage.setItem(LAST_SELECTED_TENANT_ID_KEY, tenantId);
  } else {
    localStorage.removeItem(ACTIVE_TENANT_ID_KEY);
  }
  notifyTenantContextChanged();
}

export function clearActiveTenantContext(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACTIVE_TENANT_ID_KEY);
  localStorage.removeItem(LAST_SELECTED_TENANT_ID_KEY);
  notifyTenantContextChanged();
}

export function getActiveTenantContext(): { tenantId: string | null } {
  if (typeof window === 'undefined') {
    return { tenantId: null };
  }
  const tenantId = localStorage.getItem(ACTIVE_TENANT_ID_KEY) || localStorage.getItem(LAST_SELECTED_TENANT_ID_KEY);
  return { tenantId };
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
    const messages = detail
      .map((item) => {
        const entry = item as { loc?: unknown; msg?: unknown; type?: unknown };
        const loc = Array.isArray(entry?.loc) ? entry.loc.join('.') : '';
        const msg = typeof entry?.msg === 'string' ? entry.msg : '';
        const type = typeof entry?.type === 'string' ? entry.type : '';
        const parts = [loc, msg, type].filter(Boolean);
        return parts.join(' | ');
      })
      .filter((value) => value.length > 0);
    if (messages.length > 0) return messages.join(' || ');
  }

  if (detail && typeof detail === 'object') {
    try {
      return JSON.stringify(detail);
    } catch {
      return fallback;
    }
  }

  return error.message || fallback;
}

export default api;
