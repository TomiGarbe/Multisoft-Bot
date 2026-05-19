import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { Tenant } from '@/types/tenant';
import type { User } from '@/types/access';
import { AUTH_SESSION_CHANGED_EVENT, getAuthContext, getToken } from '@/services/auth';
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
  permissionCodes: string[];
  isSuperAdmin: boolean;
  canSwitchTenant: boolean;
  activeTenantId: string | null;
  activeTenant: Tenant | null;
  setTenant: (tenantId: string) => void;
  refresh: () => Promise<void>;
}

const TenantContext = createContext<TenantContextValue | null>(null);

export function TenantProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);
  const refreshRequestIdRef = useRef(0);

  const resolveInitialTenantId = useCallback((tenantList: Tenant[]): string | null => {
    const tenantSet = new Set(tenantList.map((tenant) => tenant.id));
    const stored = getActiveTenantContext();
    const fallbackTenantId = tenantList[0]?.id ?? null;
    return stored.tenantId && tenantSet.has(stored.tenantId) ? stored.tenantId : fallbackTenantId;
  }, []);

  const refresh = useCallback(async () => {
    const requestId = ++refreshRequestIdRef.current;
    const tokenAtStart = getToken();
    if (!tokenAtStart) {
      setUser(null);
      setTenants([]);
      setActiveTenantId(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const context = await getAuthContext();
      const tokenNow = getToken();
      const isStale = requestId !== refreshRequestIdRef.current || !tokenNow || tokenNow !== tokenAtStart;
      if (isStale) {
        return;
      }
      const profile = context.user;
      const tenantList = context.tenants;

      setUser(profile);
      setTenants(tenantList);
      const nextTenantId = resolveInitialTenantId(tenantList);

      setActiveTenantId(nextTenantId);
      setActiveTenantContext(nextTenantId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el contexto de tenant');
      setUser(null);
      setTenants([]);
      setActiveTenantId(null);
    } finally {
      setLoading(false);
    }
  }, [resolveInitialTenantId]);

  useEffect(() => {
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

  useEffect(() => {
    const handler = () => {
      void refresh();
    };
    if (typeof window !== 'undefined') {
      window.addEventListener(AUTH_SESSION_CHANGED_EVENT, handler);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener(AUTH_SESSION_CHANGED_EVENT, handler);
      }
    };
  }, [refresh]);

  useEffect(() => {
    if (tenants.length === 0) return;
    const hasCurrent = activeTenantId && tenants.some((tenant) => tenant.id === activeTenantId);
    if (hasCurrent) return;
    const nextTenantId = resolveInitialTenantId(tenants);
    if (!nextTenantId) return;
    setActiveTenantId(nextTenantId);
    setActiveTenantContext(nextTenantId);
  }, [activeTenantId, resolveInitialTenantId, tenants]);

  const setTenant = useCallback((tenantId: string) => {
    const nextTenantId = tenantId.trim();
    if (!nextTenantId) return;
    if (!tenants.some((tenant) => tenant.id === nextTenantId)) return;
    setActiveTenantId(nextTenantId);
    setActiveTenantContext(nextTenantId);
  }, [tenants]);

  const value = useMemo<TenantContextValue>(() => {
    const activeTenant = tenants.find((tenant) => tenant.id === activeTenantId) ?? null;
    const permissionCodes = (user?.permissions ?? []).map((permission) => permission.code);
    const isSuperAdmin = user?.user_type === 'Backdoor' || user?.is_backdoor === true;
    const canSwitchTenant = tenants.length > 1;

    return {
      loading,
      error,
      user,
      tenants,
      permissionCodes,
      isSuperAdmin,
      canSwitchTenant,
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
