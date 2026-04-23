import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getApiErrorMessage } from '@/services/api';
import { getToken } from '@/services/auth';
import { deleteUser, getUsers } from '@/services/users';
import type { User } from '@/types/access';

export function useUsersPage(toast: any) {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  useEffect(() => {
    if (!hasToken) {
      router.replace('/login');
    }
  }, [hasToken, router]);

  const loadUsers = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await getUsers();
      setUsers(result);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load users.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void loadUsers();
  }, [hasToken, loadUsers]);

  const openCreate = () => {
    setSelectedUser(null);
    setIsFormOpen(true);
  };

  const openEdit = (user: User) => {
    setSelectedUser(user);
    setIsFormOpen(true);
  };

  const handleDelete = async (user: User) => {
    const confirmed = window.confirm(
      `Delete user "${user.name}"? This action cannot be undone.`,
    );
    if (!confirmed) return;

    try {
      setIsDeletingId(user.id);
      await deleteUser(user.id);
      toast.success('User deleted successfully.');
      await loadUsers();
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Unable to delete user.'));
    } finally {
      setIsDeletingId(null);
    }
  };

  const statusLabel = useMemo(
    () => (user: User) => (user.is_active === false ? 'Inactive' : 'Active'),
    [],
  );

  return {
    hasToken,
    users,
    isLoading,
    error,
    isDeletingId,
    isFormOpen,
    selectedUser,
    openCreate,
    openEdit,
    handleDelete,
    statusLabel,
    setIsFormOpen,
    loadUsers,
  };
}