import { Menu } from 'lucide-react';
import { useRouter } from 'next/router';
import { getPageTitle } from '@/lib/navigation';
import TenantSwitcher from '@/components/tenants/TenantSwitcher';

interface HeaderProps {
  onOpenSidebar: () => void;
}

export default function Header({ onOpenSidebar }: HeaderProps) {
  const { pathname } = useRouter();
  const title = getPageTitle(pathname);

  return (
    <header className="header sticky top-0 z-[1000] flex h-[var(--layout-header-height)] items-center gap-3 border-b border-slate-200 bg-white px-4 md:px-6">
      <button
        type="button"
        onClick={onOpenSidebar}
        className="mr-1 inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 text-slate-700 hover:bg-slate-50 lg:hidden"
        aria-label="Abrir menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex-1">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      </div>
      <TenantSwitcher />
    </header>
  );
}
