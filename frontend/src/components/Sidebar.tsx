'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface SidebarProps {
  onLogout: () => void;
}

export default function Sidebar({ onLogout }: SidebarProps) {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Multisoft Bot</h1>
        <p className="text-gray-400 text-sm mt-1">Admin Panel</p>
      </div>

      <nav className="space-y-2 mb-8">
        <Link
          href="/dashboard"
          className={`block px-4 py-2 rounded transition ${
            isActive('/dashboard')
              ? 'bg-blue-600'
              : 'hover:bg-gray-800'
          }`}
        >
          Dashboard
        </Link>
        <Link
          href="/users"
          className={`block px-4 py-2 rounded transition ${
            isActive('/users')
              ? 'bg-blue-600'
              : 'hover:bg-gray-800'
          }`}
        >
          Users
        </Link>
        <Link
          href="/roles"
          className={`block px-4 py-2 rounded transition ${
            isActive('/roles')
              ? 'bg-blue-600'
              : 'hover:bg-gray-800'
          }`}
        >
          Roles
        </Link>
        <Link
          href="/permissions"
          className={`block px-4 py-2 rounded transition ${
            isActive('/permissions')
              ? 'bg-blue-600'
              : 'hover:bg-gray-800'
          }`}
        >
          Permissions
        </Link>
      </nav>

      <button
        onClick={onLogout}
        className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition"
      >
        Logout
      </button>
    </aside>
  );
}
