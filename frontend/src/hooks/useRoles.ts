import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getToken } from '@/services/auth';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { deleteRole, getRoles } from '@/services/roles';
import type { Role } from '@/types/access';

function isTenantRole(role: Role): boolean {
  const normalizedName = role.name.trim().toLowerCase();
  if (!normalizedName) return false;
  if (normalizedName.includes('admin')) return false;
  if (normalizedName.includes('backdoor')) return false;
  if (normalizedName === 'user' || normalizedName === 'global user') return false;
  return true;
}

export function useRoles(toast?: { success: (message: string) => void; error: (message: string) => void }) {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  useEffect(() => {
    if (!hasToken) router.replace('/login');
  }, [hasToken, router]);

  const fetchRoles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getRoles();
      setRoles(result.filter(isTenantRole));
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar los roles.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void fetchRoles();
  }, [hasToken, fetchRoles]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      if (hasToken) void fetchRoles();
    };
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
  }, [hasToken, fetchRoles]);

  const createRole = () => {
    setSelectedRole(null);
    setIsFormOpen(true);
  };

  const updateRole = (role: Role) => {
    setSelectedRole(role);
    setIsFormOpen(true);
  };

  const deleteRoleItem = async (role: Role) => {
    const confirmed = window.confirm(`Eliminar el rol "${role.name}"? Esta accion no se puede deshacer.`);
    if (!confirmed) return;

    try {
      setDeletingId(role.id);
      await deleteRole(role.id);
      toast?.success('Rol eliminado correctamente.');
      await fetchRoles();
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo eliminar el rol.');
      if (toast) toast.error(message);
      else setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  return {
    hasToken,
    roles,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedRole,
    fetchRoles,
    createRole,
    updateRole,
    deleteRole: deleteRoleItem,
    setIsFormOpen,
  };
}
