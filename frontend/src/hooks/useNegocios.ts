import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { useAuthToken } from '@/hooks/useAuthToken';
import { deleteTenant, getTenants } from '@/services/tenants';
import type { Tenant } from '@/types/tenant';

export function useNegocios(toast?: { success: (message: string) => void; error: (message: string) => void }) {
  const router = useRouter();
  const { authResolved, hasToken } = useAuthToken();

  const [negocios, setNegocios] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedNegocio, setSelectedNegocio] = useState<Tenant | null>(null);

  useEffect(() => {
    if (!authResolved) return;
    if (!hasToken) {
      router.replace('/login');
    }
  }, [authResolved, hasToken, router]);

  const fetchNegocios = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getTenants();
      setNegocios(result);
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar los negocios.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void fetchNegocios();
  }, [hasToken, fetchNegocios]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      if (hasToken) void fetchNegocios();
    };
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
  }, [hasToken, fetchNegocios]);

  const openCreateNegocio = () => {
    setSelectedNegocio(null);
    setIsFormOpen(true);
  };

  const openEditNegocio = (negocio: Tenant) => {
    setSelectedNegocio(negocio);
    setIsFormOpen(true);
  };

  const deleteNegocio = async (negocio: Tenant) => {
    const confirmed = window.confirm(`Eliminar el negocio "${negocio.name}"? Esta accion no se puede deshacer.`);
    if (!confirmed) return;

    try {
      setDeletingId(negocio.id);
      await deleteTenant(negocio.id);
      toast?.success('Negocio eliminado correctamente.');
      await fetchNegocios();
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo eliminar el negocio.');
      if (toast) toast.error(message);
      else setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  return {
    authResolved,
    hasToken,
    negocios,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedNegocio,
    fetchNegocios,
    createNegocio: openCreateNegocio,
    updateNegocio: openEditNegocio,
    deleteNegocio,
    setIsFormOpen,
  };
}
