import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import { NAV_ITEMS } from '@/lib/navigation';

export default function Sidebar() {
  const { pathname } = useRouter();
  const { user, logout } = useAuth();

  const initials = (user?.name ?? 'U')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');

  return (
    <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col">
      <div className="flex h-[var(--layout-header-height)] items-center border-b border-slate-200 px-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Multisoft Bot</h1>
          <p className="text-sm text-slate-500">Panel de administración</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1.5 p-4">
        {NAV_ITEMS.map((item) => {
          const isActive =
            pathname === item.path || (item.path === '/dashboard' && pathname === '/');
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              href={item.path}
              className={`flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <Icon className="h-5 w-5 shrink-0" />
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
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
