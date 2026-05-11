import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { getToken } from '@/services/auth';
import { deleteUser, getUsers, updateUser } from '@/services/users';
import type { User } from '@/types/access';

export function useUsers(toast?: { success: (message: string) => void; error: (message: string) => void }) {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const [usuarios, setUsuarios] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

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
      setUsuarios(result.filter((user) => !user.is_backdoor));
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar los usuarios.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void fetchUsuarios();
  }, [hasToken, fetchUsuarios]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      if (hasToken) void fetchUsuarios();
    };
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
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
    const confirmed = window.confirm(`Eliminar el usuario "${usuario.name}"? Esta accion no se puede deshacer.`);
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

  const toggleUsuarioEstado = async (usuario: User) => {
    try {
      setUpdatingId(usuario.id);
      await updateUser(usuario.id, { is_active: !(usuario.is_active ?? true) });
      toast?.success((usuario.is_active ?? true) ? 'Usuario desactivado.' : 'Usuario activado.');
      await fetchUsuarios();
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo actualizar el estado del usuario.');
      if (toast) toast.error(message);
      else setError(message);
    } finally {
      setUpdatingId(null);
    }
  };

  const resetUsuarioPassword = async (usuario: User) => {
    const nextPassword = window.prompt(`Nueva contrasena para ${usuario.email}`)?.trim() ?? '';
    if (!nextPassword) return;

    if (nextPassword.length < 8 || !/[A-Z]/.test(nextPassword) || !/[a-z]/.test(nextPassword) || !/\d/.test(nextPassword)) {
      const message = 'La contrasena debe tener al menos 8 caracteres, mayuscula, minuscula y numero.';
      if (toast) toast.error(message);
      else setError(message);
      return;
    }

    try {
      setUpdatingId(usuario.id);
      await updateUser(usuario.id, { password: nextPassword });
      toast?.success('Contrasena actualizada correctamente.');
    } catch (err) {
      const message = getApiErrorMessage(err, 'No se pudo resetear la contrasena.');
      if (toast) toast.error(message);
      else setError(message);
    } finally {
      setUpdatingId(null);
    }
  };

  const statusLabel = useMemo(() => (usuario: User) => (usuario.is_active === false ? 'Inactivo' : 'Activo'), []);

  return {
    hasToken,
    usuarios,
    loading,
    error,
    deletingId,
    updatingId,
    isFormOpen,
    selectedUsuario,
    fetchUsuarios,
    createUsuario: openCreateUsuario,
    updateUsuario: openEditUsuario,
    deleteUsuario,
    toggleUsuarioEstado,
    resetUsuarioPassword,
    statusLabel,
    setIsFormOpen,
  };
}
