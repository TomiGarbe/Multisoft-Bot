'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { clearTokens, isAuthenticated } from '@/lib/auth';
import Layout from '@/components/Layout';
import Sidebar from '@/components/Sidebar';
import Button from '@/components/Button';
import { usersApi } from '@/services/api';

interface User {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface UserFormData {
  name: string;
  email: string;
  password: string;
  is_active: boolean;
}

const INITIAL_FORM: UserFormData = {
  name: '',
  email: '',
  password: '',
  is_active: true,
};

export default function UsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<UserFormData>(INITIAL_FORM);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login');
      return;
    }

    void loadUsers();
  }, [router]);

  const loadUsers = async () => {
    setLoadingList(true);
    try {
      const response = await usersApi.getAll();
      setUsers(response.data);
      setError('');
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'No se pudieron cargar los usuarios';
      setError(message);
    } finally {
      setLoadingList(false);
    }
  };

  const resetForm = () => {
    setFormData(INITIAL_FORM);
    setEditingId(null);
    setShowForm(false);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    const payload = {
      ...formData,
      password: formData.password.trim(),
    };

    try {
      if (editingId) {
        const updatePayload = payload.password
          ? payload
          : { name: payload.name, email: payload.email, is_active: payload.is_active };
        await usersApi.update(editingId, updatePayload);
      } else {
        await usersApi.create(payload);
      }

      resetForm();
      await loadUsers();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'No se pudo guardar el usuario';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    const confirmed = window.confirm('¿Eliminar este usuario?');
    if (!confirmed) {
      return;
    }

    setDeletingId(id);
    setError('');

    try {
      await usersApi.delete(id);
      await loadUsers();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        'No se pudo eliminar el usuario';
      setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleEdit = (user: User) => {
    setEditingId(user.id);
    setFormData({
      name: user.name,
      email: user.email,
      password: '',
      is_active: user.is_active,
    });
    setShowForm(true);
  };

  const handleToggleForm = () => {
    if (showForm) {
      resetForm();
      return;
    }

    setEditingId(null);
    setFormData(INITIAL_FORM);
    setShowForm(true);
  };

  const handleLogout = () => {
    clearTokens();
    router.push('/login');
  };

  return (
    <Layout sidebar={<Sidebar onLogout={handleLogout} />}>
      <div className="p-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Usuarios</h1>
          <Button onClick={handleToggleForm} variant="primary">
            {showForm ? 'Cancelar' : 'Crear usuario'}
          </Button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {showForm && (
          <div className="mb-8 rounded-lg bg-white p-6 shadow">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">Nombre</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Password {editingId && '(vacío para conservar actual)'}
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2"
                  required={!editingId}
                />
              </div>

              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
                Activo
              </label>

              <div className="flex gap-2">
                <Button type="submit" variant="primary" disabled={saving}>
                  {saving ? 'Guardando...' : editingId ? 'Actualizar' : 'Crear'}
                </Button>
                <Button type="button" variant="secondary" onClick={resetForm}>
                  Cancelar
                </Button>
              </div>
            </form>
          </div>
        )}

        <div className="overflow-hidden rounded-lg bg-white shadow">
          {loadingList ? (
            <div className="p-8 text-center text-gray-500">Cargando usuarios...</div>
          ) : users.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No hay usuarios</div>
          ) : (
            <table className="w-full">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Nombre</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Email</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Estado</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{user.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{user.email}</td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-medium ${
                          user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="space-x-2 px-6 py-4 text-sm">
                      <Button onClick={() => handleEdit(user)} variant="secondary" size="sm">
                        Editar
                      </Button>
                      <Button
                        onClick={() => handleDelete(user.id)}
                        variant="danger"
                        size="sm"
                        disabled={deletingId === user.id}
                      >
                        {deletingId === user.id ? 'Eliminando...' : 'Eliminar'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  );
}
