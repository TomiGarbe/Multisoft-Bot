'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, clearTokens } from '@/lib/auth';
import Layout from '@/components/Layout';
import Sidebar from '@/components/Sidebar';
import Button from '@/components/Button';
import { rolesApi } from '@/services/api';

interface Role {
  id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export default function RolesPage() {
  const router = useRouter();
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
    } else {
      loadRoles();
    }
  }, [router]);

  const loadRoles = async () => {
    setLoading(true);
    try {
      const response = await rolesApi.getAll();
      setRoles(response.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load roles');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (editingId) {
        await rolesApi.update(editingId, formData);
      } else {
        await rolesApi.create(formData);
      }
      setFormData({ name: '', description: '' });
      setEditingId(null);
      setShowForm(false);
      loadRoles();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save role');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure?')) {
      try {
        await rolesApi.delete(id);
        loadRoles();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to delete role');
      }
    }
  };

  const handleEdit = (role: Role) => {
    setEditingId(role.id);
    setFormData({
      name: role.name,
      description: role.description || '',
    });
    setShowForm(true);
  };

  const handleLogout = () => {
    clearTokens();
    router.push('/login');
  };

  return (
    <Layout sidebar={<Sidebar onLogout={handleLogout} />}>
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Roles</h1>
          <Button
            onClick={() => {
              setEditingId(null);
              setFormData({ name: '', description: '' });
              setShowForm(!showForm);
            }}
            variant="primary"
          >
            {showForm ? 'Cancel' : 'Add Role'}
          </Button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {showForm && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-gray-700 font-medium mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-gray-700 font-medium mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                />
              </div>

              <div className="flex gap-2">
                <Button type="submit" variant="primary" disabled={loading}>
                  {loading ? 'Saving...' : editingId ? 'Update' : 'Create'}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        )}

        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading && !roles.length ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : roles.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No roles found</div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Description</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Type</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {roles.map((role) => (
                  <tr key={role.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{role.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{role.description || '-'}</td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          role.is_system
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {role.is_system ? 'System' : 'Custom'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm space-x-2">
                      {!role.is_system && (
                        <>
                          <Button
                            onClick={() => handleEdit(role)}
                            variant="secondary"
                            size="sm"
                          >
                            Edit
                          </Button>
                          <Button
                            onClick={() => handleDelete(role.id)}
                            variant="danger"
                            size="sm"
                          >
                            Delete
                          </Button>
                        </>
                      )}
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
