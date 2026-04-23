import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/services/auth';
import { getApiErrorMessage } from '@/services/api';
import { getRoles, deleteRole } from '@/services/roles';
import type { Role } from '@/types/access';

export function useRolesPage(toast: any) {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  useEffect(() => {
    if (!hasToken) {
      router.replace('/login');
    }
  }, [hasToken, router]);

  const loadRoles = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await getRoles();
      setRoles(result);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load roles.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void loadRoles();
  }, [hasToken, loadRoles]);

  const openCreate = () => {
    setSelectedRole(null);
    setIsFormOpen(true);
  };

  const openEdit = (role: Role) => {
    setSelectedRole(role);
    setIsFormOpen(true);
  };

  const handleDelete = async (role: Role) => {
    const confirmed = window.confirm(
      `Delete role "${role.name}"? This action cannot be undone.`,
    );
    if (!confirmed) return;

    try {
      setIsDeletingId(role.id);
      await deleteRole(role.id);
      toast.success('Role deleted successfully.');
      await loadRoles();
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Unable to delete role.'));
    } finally {
      setIsDeletingId(null);
    }
  };

  return {
    hasToken,
    roles,
    isLoading,
    error,
    isDeletingId,
    isFormOpen,
    selectedRole,
    openCreate,
    openEdit,
    handleDelete,
    setIsFormOpen,
    loadRoles,
  };
}