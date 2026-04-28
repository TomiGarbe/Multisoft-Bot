'use client';

import { useRouter } from 'next/router';
import { getPageTitle } from '@/lib/navigation';

export default function Header() {
  const { pathname } = useRouter();
  const title = getPageTitle(pathname);

  return (
    <header className="flex h-[var(--layout-header-height)] items-center border-b border-slate-200 bg-white px-6">
      <div className="flex-1">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      </div>
    </header>
  );
}
