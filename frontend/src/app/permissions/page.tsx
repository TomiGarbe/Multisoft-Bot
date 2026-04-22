'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, clearTokens } from '@/lib/auth';
import Layout from '@/components/Layout';
import Sidebar from '@/components/Sidebar';
import Button from '@/components/Button';
import { permissionsApi } from '@/services/api';

interface Permission {
  id: string;
  code: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export default function PermissionsPage() {
  const router = useRouter();
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
    } else {
      loadPermissions();
    }
  }, [router]);

  const loadPermissions = async () => {
    setLoading(true);
    try {
      const response = await permissionsApi.getAll();
      setPermissions(response.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load permissions');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (editingId) {
        await permissionsApi.update(editingId, formData);
      } else {
        await permissionsApi.create(formData);
      }
      setFormData({ code: '', name: '', description: '' });
      setEditingId(null);
      setShowForm(false);
      loadPermissions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save permission');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure?')) {
      try {
        await permissionsApi.delete(id);
        loadPermissions();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to delete permission');
      }
    }
  };

  const handleEdit = (permission: Permission) => {
    setEditingId(permission.id);
    setFormData({
      code: permission.code,
      name: permission.name,
      description: permission.description || '',
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
          <h1 className="text-3xl font-bold text-gray-900">Permissions</h1>
          <Button
            onClick={() => {
              setEditingId(null);
              setFormData({ code: '', name: '', description: '' });
              setShowForm(!showForm);
            }}
            variant="primary"
          >
            {showForm ? 'Cancel' : 'Add Permission'}
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
                <label className="block text-gray-700 font-medium mb-2">Code</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  placeholder="e.g., USER_CREATE"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg font-mono"
                  required
                />
              </div>

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
          {loading && !permissions.length ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : permissions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No permissions found</div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Code</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Description</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {permissions.map((permission) => (
                  <tr key={permission.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-mono text-gray-900">{permission.code}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{permission.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{permission.description || '-'}</td>
                    <td className="px-6 py-4 text-sm space-x-2">
                      <Button
                        onClick={() => handleEdit(permission)}
                        variant="secondary"
                        size="sm"
                      >
                        Edit
                      </Button>
                      <Button
                        onClick={() => handleDelete(permission.id)}
                        variant="danger"
                        size="sm"
                      >
                        Delete
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
