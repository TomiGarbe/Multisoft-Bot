import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { getApiErrorMessage } from '@/services/api';
import { getToken } from '@/services/auth';
import { deleteUser, getUsers } from '@/services/users';
import type { User } from '@/types/access';

export function useUsuarios(toast?: { success: (message: string) => void; error: (message: string) => void }) {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const [usuarios, setUsuarios] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedUsuario, setSelectedUsuario] = useState<User | null>(null);

  useEffect(() => {
    if (!hasToken) {
      router.replace('/login');
    }
  }, [hasToken, router]);

  const fetchUsuarios = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getUsers();
      setUsuarios(result);
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar los usuarios.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void fetchUsuarios();
  }, [hasToken, fetchUsuarios]);

  const openCreateUsuario = () => {
    setSelectedUsuario(null);
    setIsFormOpen(true);
  };

  const openEditUsuario = (usuario: User) => {
    setSelectedUsuario(usuario);
    setIsFormOpen(true);
  };

  const deleteUsuario = async (usuario: User) => {
    const confirmed = window.confirm(`�Eliminar el usuario "${usuario.name}"? Esta acción no se puede deshacer.`);
    if (!confirmed) return;

    try {
      setDeletingId(usuario.id);
      await deleteUser(usuario.id);
      toast?.success('Usuario eliminado correctamente.');
      await fetchUsuarios();
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo eliminar el usuario.');
      if (toast) toast.error(message);
      else setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  const statusLabel = useMemo(() => (usuario: User) => (usuario.is_active === false ? 'Inactivo' : 'Activo'), []);

  return {
    hasToken,
    usuarios,
    loading,
    error,
    deletingId,
    isFormOpen,
    selectedUsuario,
    fetchUsuarios,
    createUsuario: openCreateUsuario,
    updateUsuario: openEditUsuario,
    deleteUsuario,
    statusLabel,
    setIsFormOpen,
  };
}
