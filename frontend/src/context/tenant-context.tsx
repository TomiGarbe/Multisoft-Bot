import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { Tenant } from '@/types/tenant';
import type { User } from '@/types/access';
import { getTenants } from '@/services/tenants';
import { getCurrentUser, getToken } from '@/services/auth';
import {
  getActiveTenantContext,
  setActiveTenantContext,
  type ActiveScope,
  TENANT_CONTEXT_CHANGED_EVENT,
} from '@/services/api';

interface TenantContextValue {
  loading: boolean;
  error: string | null;
  user: User | null;
  tenants: Tenant[];
  activeTenantId: string | null;
  activeTenant: Tenant | null;
  scope: ActiveScope;
  canUseGlobalScope: boolean;
  setTenant: (tenantId: string) => void;
  setScope: (scope: ActiveScope) => void;
  refresh: () => Promise<void>;
}

const TenantContext = createContext<TenantContextValue | null>(null);

function isSuperAdmin(user: User | null): boolean {
  return !!user && (user.user_type === 'BACKDOOR' || user.is_backdoor === true);
}

export function TenantProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);
  const [scope, setScopeState] = useState<ActiveScope>('tenant');

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setTenants([]);
      setActiveTenantId(null);
      setScopeState('tenant');
      setLoading(false);
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
      const nextScope: ActiveScope = stored.scope === 'global' && isSuperAdmin(profile) ? 'global' : 'tenant';

      setActiveTenantId(nextTenantId);
      setScopeState(nextScope);
      setActiveTenantContext(nextTenantId, nextScope);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el contexto de tenant');
      setUser(null);
      setTenants([]);
      setActiveTenantId(null);
      setScopeState('tenant');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const handler = () => {
      const current = getActiveTenantContext();
      setActiveTenantId(current.tenantId);
      setScopeState(current.scope);
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
    setScopeState('tenant');
    setActiveTenantContext(nextTenantId, 'tenant');
  }, []);

  const setScope = useCallback(
    (nextScope: ActiveScope) => {
      if (nextScope === 'global' && !isSuperAdmin(user)) {
        return;
      }
      setScopeState(nextScope);
      setActiveTenantContext(activeTenantId, nextScope);
    },
    [activeTenantId, user],
  );

  const value = useMemo<TenantContextValue>(() => {
    const activeTenant = tenants.find((tenant) => tenant.id === activeTenantId) ?? null;

    return {
      loading,
      error,
      user,
      tenants,
      activeTenantId,
      activeTenant,
      scope,
      canUseGlobalScope: isSuperAdmin(user),
      setTenant,
      setScope,
      refresh,
    };
  }, [loading, error, user, tenants, activeTenantId, scope, setTenant, setScope, refresh]);

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenantContext(): TenantContextValue {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenantContext must be used within TenantProvider');
  }
  return context;
}
