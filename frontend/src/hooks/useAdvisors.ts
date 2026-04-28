import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getToken } from '@/services/auth';
import { getApiErrorMessage } from '@/services/api';
import { deleteRole, getRoles } from '@/services/roles';
import type { Role } from '@/types/access';

export function useAdvisors(toast?: { success: (message: string) => void; error: (message: string) => void }) {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const [advisors, setAdvisors] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedAdvisor, setSelectedAdvisor] = useState<Role | null>(null);

  useEffect(() => {
    if (!hasToken) router.replace('/login');
  }, [hasToken, router]);

  const fetchAdvisors = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getRoles();
      setAdvisors(result);
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar los advisors.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void fetchAdvisors();
  }, [hasToken, fetchAdvisors]);

  const createAdvisor = () => {
    setSelectedAdvisor(null);
    setIsFormOpen(true);
  };

  const updateAdvisor = (advisor: Role) => {
    setSelectedAdvisor(advisor);
    setIsFormOpen(true);
  };

  const deleteAdvisor = async (advisor: Role) => {
    const confirmed = window.confirm(`�Eliminar el advisor \"${advisor.name}\"? Esta acción no se puede deshacer.`);
    if (!confirmed) return;

    try {
      setDeletingId(advisor.id);
      await deleteRole(advisor.id);
      toast?.success('Advisor eliminado correctamente.');
      await fetchAdvisors();
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo eliminar el advisor.');
      if (toast) toast.error(message);
      else setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  return {
    hasToken,
    advisors,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedAdvisor,
    fetchAdvisors,
    createAdvisor,
    updateAdvisor,
    deleteAdvisor,
    setIsFormOpen,
  };
}
