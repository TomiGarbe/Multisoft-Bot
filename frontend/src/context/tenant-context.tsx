import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { Tenant } from '@/types/tenant';
import type { User } from '@/types/access';
import { getTenants } from '@/services/tenants';
import { getCurrentUser, getToken } from '@/services/auth';
import {
  getActiveTenantContext,
  setActiveTenantContext,
  TENANT_CONTEXT_CHANGED_EVENT,
} from '@/services/api';

interface TenantContextValue {
  loading: boolean;
  error: string | null;
  user: User | null;
  tenants: Tenant[];
  activeTenantId: string | null;
  activeTenant: Tenant | null;
  setTenant: (tenantId: string) => void;
  refresh: () => Promise<void>;
}

const TenantContext = createContext<TenantContextValue | null>(null);
const hydrationDebugEnabled = process.env.NEXT_PUBLIC_DEBUG_HYDRATION === '1';

function hydrationLog(message: string, payload?: Record<string, unknown>) {
  if (!hydrationDebugEnabled) return;
  if (payload) {
    console.info(`[HYDRATION] ${message}`, payload);
    return;
  }
  console.info(`[HYDRATION] ${message}`);
}

export function TenantProvider({ children }: { children: ReactNode }) {
  hydrationLog(typeof window === 'undefined' ? 'server render tenant provider' : 'client render tenant provider');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    hydrationLog('tenant refresh start');
    if (!getToken()) {
      setUser(null);
      setTenants([]);
      setActiveTenantId(null);
      setLoading(false);
      hydrationLog('tenant refresh no token');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const [profile, tenantList] = await Promise.all([getCurrentUser(), getTenants()]);

      setUser(profile);
      setTenants(tenantList);

      const stored = getActiveTenantContext();
      const tenantSet = new Set(tenantList.map((tenant) => tenant.id));
      const fallbackTenantId = tenantList[0]?.id ?? null;
      const nextTenantId = stored.tenantId && tenantSet.has(stored.tenantId) ? stored.tenantId : fallbackTenantId;

      setActiveTenantId(nextTenantId);
      setActiveTenantContext(nextTenantId);
      hydrationLog('tenant loaded', { tenantCount: tenantList.length, activeTenantId: nextTenantId });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el contexto de tenant');
      setUser(null);
      setTenants([]);
      setActiveTenantId(null);
      hydrationLog('tenant refresh error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    hydrationLog('client mounted tenant provider');
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const handler = () => {
      const current = getActiveTenantContext();
      setActiveTenantId(current.tenantId);
    };

    if (typeof window !== 'undefined') {
      window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    }

    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
      }
    };
  }, []);

  const setTenant = useCallback((tenantId: string) => {
    const nextTenantId = tenantId.trim();
    setActiveTenantId(nextTenantId);
    setActiveTenantContext(nextTenantId);
  }, []);

  const value = useMemo<TenantContextValue>(() => {
    const activeTenant = tenants.find((tenant) => tenant.id === activeTenantId) ?? null;

    return {
      loading,
      error,
      user,
      tenants,
      activeTenantId,
      activeTenant,
      setTenant,
      refresh,
    };
  }, [loading, error, user, tenants, activeTenantId, setTenant, refresh]);

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenantContext(): TenantContextValue {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenantContext must be used within TenantProvider');
  }
  return context;
}
