import { useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/router';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { useTenantContext } from '@/context/tenant-context';
import { NAV_ITEMS, canAccessPath, canAccessSection } from '@/lib/navigation';

interface AppLayoutProps {
  children: ReactNode;
  scrollMain?: boolean;
}

export default function AppLayout({ children, scrollMain = true }: AppLayoutProps) {
  const router = useRouter();
  const { loading, permissionCodes, isSuperAdmin } = useTenantContext();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const hasRouteAccess = canAccessPath(permissionCodes, router.pathname, isSuperAdmin);
  const firstAllowedRoute = NAV_ITEMS.find((item) => canAccessSection(permissionCodes, item, isSuperAdmin))?.path ?? null;

  useEffect(() => {
    if (loading) return;
    if (hasRouteAccess) return;
    if (!firstAllowedRoute) return;
    if (router.pathname === firstAllowedRoute) return;
    void router.replace(firstAllowedRoute);
  }, [loading, hasRouteAccess, firstAllowedRoute, router]);

  return (
    <div className="app flex h-full min-h-0 overflow-hidden bg-slate-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="layout flex h-full min-h-0 min-w-0 flex-1 flex-col lg:pl-64">
        <Header onOpenSidebar={() => setSidebarOpen(true)} />
        <main className={`main flex min-h-0 flex-1 flex-col overflow-x-hidden ${scrollMain ? 'overflow-y-auto' : 'overflow-hidden'}`}>
          {loading ? (
            <div className="flex h-full min-h-[260px] items-center justify-center text-sm text-slate-500">Cargando acceso...</div>
          ) : hasRouteAccess ? (
            children
          ) : (
            <div className="mx-auto my-12 w-full max-w-xl rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
              No tienes permisos para acceder a esta seccion.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
