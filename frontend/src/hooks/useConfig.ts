import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { useAuthToken } from '@/hooks/useAuthToken';
import { deleteChannel, getChannels } from '@/services/channels';
import type { Channel } from '@/types/channel';

export function useConfig(toast?: { success: (message: string) => void; error: (message: string) => void }) {
  const router = useRouter();
  const { authResolved, hasToken } = useAuthToken();

  const [configItems, setConfigItems] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedConfigItem, setSelectedConfigItem] = useState<Channel | null>(null);

  useEffect(() => {
    if (!authResolved) return;
    if (!hasToken) router.replace('/login');
  }, [authResolved, hasToken, router]);

  const fetchConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getChannels();
      setConfigItems(result);
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudo cargar la configuracion.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void fetchConfig();
  }, [hasToken, fetchConfig]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      if (hasToken) void fetchConfig();
    };
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
  }, [hasToken, fetchConfig]);

  const createConfig = () => {
    setSelectedConfigItem(null);
    setIsFormOpen(true);
  };

  const updateConfig = (item: Channel) => {
    setSelectedConfigItem(item);
    setIsFormOpen(true);
  };

  const deleteConfig = async (item: Channel) => {
    const confirmed = window.confirm(`Eliminar la configuracion \"${item.name}\"? Esta accion no se puede deshacer.`);
    if (!confirmed) return;

    try {
      setDeletingId(item.id);
      await deleteChannel(item.id);
      toast?.success('Configuracion eliminada correctamente.');
      await fetchConfig();
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo eliminar la configuracion.');
      if (toast) toast.error(message);
      else setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  return {
    authResolved,
    hasToken,
    configItems,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedConfigItem,
    fetchConfig,
    createConfig,
    updateConfig,
    deleteConfig,
    setIsFormOpen,
  };
}
