'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { isAuthenticated, clearTokens } from '@/lib/auth';
import Layout from '@/components/Layout';
import Sidebar from '@/components/Sidebar';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
    }
  }, [router]);

  const handleLogout = () => {
    clearTokens();
    router.push('/login');
  };

  return (
    <Layout sidebar={<Sidebar onLogout={handleLogout} />}>
      <div className="p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Dashboard</h1>
        <p className="text-gray-600 mb-8">Welcome to Multisoft Bot Admin Panel</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Users</h3>
            <p className="text-gray-600">Manage system users</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Roles</h3>
            <p className="text-gray-600">Manage user roles</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Permissions</h3>
            <p className="text-gray-600">Manage permissions</p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
