import { useCallback, useEffect, useState } from 'react';
import { TENANT_CONTEXT_CHANGED_EVENT, getApiErrorMessage } from '@/services/api';
import { loadDashboardData } from '@/dashboard/services/dashboard';
import type { DashboardData, DashboardScope } from '@/dashboard/types';

export function useDashboardData(scope: DashboardScope, canUseGlobalScope: boolean, enabled = true) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const next = await loadDashboardData({ scope, canUseGlobalScope });
      setData(next);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar las metricas del dashboard'));
    } finally {
      setLoading(false);
    }
  }, [enabled, scope, canUseGlobalScope]);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }
    void load();
  }, [enabled, load]);

  useEffect(() => {
    if (!enabled) return;
    if (typeof window === 'undefined') return;
    const handler = () => {
      void load();
    };

    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => {
      window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    };
  }, [enabled, load]);

  return {
    data,
    loading,
    error,
    retry: load,
  };
}
