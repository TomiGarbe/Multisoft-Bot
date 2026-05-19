import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { useTenantContext } from '@/context/tenant-context';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { useAuthToken } from '@/hooks/useAuthToken';
import {
  createIntegration,
  deleteIntegration,
  getIntegration,
  getIntegrations,
  setIntegrationEnabled,
  testIntegration,
  updateIntegration,
} from '@/services/integrations';
import type { IntegrationItem, IntegrationListItem, IntegrationPayload, IntegrationTestResponse } from '@/types/integration';

export function useIntegrations(toast?: { success: (message: string) => void; error: (message: string) => void }) {
  const router = useRouter();
  const { user } = useTenantContext();
  const { authResolved, hasToken } = useAuthToken();

  const permissionSet = useMemo(() => new Set((user?.permissions ?? []).map((p) => p.code)), [user?.permissions]);
  const canRead = permissionSet.has('bot_actions.read');
  const canCreate = permissionSet.has('bot_actions.create');
  const canUpdate = permissionSet.has('bot_actions.update');
  const canDelete = permissionSet.has('bot_actions.delete');

  const [items, setItems] = useState<IntegrationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<IntegrationItem | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [workingId, setWorkingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<IntegrationTestResponse | null>(null);

  useEffect(() => {
    if (!authResolved) return;
    if (!hasToken) {
      router.replace('/login');
    }
  }, [authResolved, hasToken, router]);

  const fetchItems = useCallback(async () => {
    if (!hasToken || !canRead) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setItems(await getIntegrations());
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar las integraciones.'));
    } finally {
      setLoading(false);
    }
  }, [hasToken, canRead]);

  useEffect(() => {
    void fetchItems();
  }, [fetchItems]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => void fetchItems();
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
  }, [fetchItems]);

  const openCreate = useCallback(() => {
    if (!canCreate) return;
    setSelectedId(null);
    setSelectedItem(null);
    setTestResult(null);
    setIsFormOpen(true);
  }, [canCreate]);

  const openEdit = useCallback(async (id: string) => {
    if (!canUpdate) return;
    try {
      setLoadingDetail(true);
      setSelectedId(id);
      setTestResult(null);
      const item = await getIntegration(id);
      setSelectedItem(item);
      setIsFormOpen(true);
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo cargar la integracion.');
      toast?.error(message);
    } finally {
      setLoadingDetail(false);
    }
  }, [canUpdate, toast]);

  const save = useCallback(async (payload: IntegrationPayload) => {
    try {
      setSubmitting(true);
      if (selectedId) {
        await updateIntegration(selectedId, payload);
        toast?.success('Integracion actualizada.');
      } else {
        await createIntegration(payload);
        toast?.success('Integracion creada.');
      }
      setIsFormOpen(false);
      setSelectedId(null);
      setSelectedItem(null);
      await fetchItems();
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo guardar la integracion.');
      toast?.error(message);
      throw new Error(message);
    } finally {
      setSubmitting(false);
    }
  }, [selectedId, toast, fetchItems]);

  const toggleEnabled = useCallback(async (item: IntegrationListItem) => {
    if (!canUpdate) return;
    try {
      setWorkingId(item.id);
      await setIntegrationEnabled(item.id, !item.enabled);
      toast?.success(item.enabled ? 'Integracion desactivada.' : 'Integracion activada.');
      await fetchItems();
    } catch (err) {
      toast?.error(getApiErrorMessage(err, 'No se pudo actualizar el estado.'));
    } finally {
      setWorkingId(null);
    }
  }, [canUpdate, toast, fetchItems]);

  const remove = useCallback(async (item: IntegrationListItem) => {
    if (!canDelete) return;
    if (!window.confirm(`Eliminar integracion \"${item.name}\"?`)) return;
    try {
      setWorkingId(item.id);
      await deleteIntegration(item.id);
      toast?.success('Integracion eliminada.');
      await fetchItems();
    } catch (err) {
      toast?.error(getApiErrorMessage(err, 'No se pudo eliminar la integracion.'));
    } finally {
      setWorkingId(null);
    }
  }, [canDelete, toast, fetchItems]);

  const runTest = useCallback(async (id: string, variables: Record<string, unknown>) => {
    try {
      setWorkingId(id);
      const result = await testIntegration(id, variables);
      setTestResult(result);
      if (result.success) toast?.success('Prueba ejecutada correctamente.');
      else toast?.error(result.error ?? 'La prueba devolvio error.');
      return result;
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo ejecutar la prueba.');
      toast?.error(message);
      throw new Error(message);
    } finally {
      setWorkingId(null);
    }
  }, [toast]);

  return {
    authResolved,
    hasToken,
    loading,
    error,
    items,
    isFormOpen,
    loadingDetail,
    selectedItem,
    selectedId,
    submitting,
    workingId,
    testResult,
    canRead,
    canCreate,
    canUpdate,
    canDelete,
    setIsFormOpen,
    openCreate,
    openEdit,
    save,
    toggleEnabled,
    remove,
    runTest,
  };
}
