'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/users', label: 'Users' },
  { href: '/roles', label: 'Roles' },
  { href: '/tenants', label: 'Negocios/Empresas' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const initials = (user?.name ?? 'U')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');

  return (
    <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col">
      <div className="border-b border-slate-200 px-6 py-6">
        <h1 className="text-xl font-bold text-slate-900">Multisoft Bot</h1>
        <p className="mt-1 text-sm text-slate-500">Admin Panel</p>
      </div>

      <nav className="flex-1 space-y-2 p-4">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-4 py-2 text-sm font-medium transition ${
                isActive
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 p-4">
        <div className="mb-4 flex items-center gap-3 rounded-lg bg-slate-50 p-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sky-100 text-sm font-semibold text-sky-700">
            {initials || 'U'}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-900">{user?.name ?? 'Usuario'}</p>
            <p className="truncate text-xs text-slate-500">{user?.email ?? 'Sin email'}</p>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 hover:text-rose-600"
        >
          Logout
        </button>
      </div>
    </aside>
  );
}
