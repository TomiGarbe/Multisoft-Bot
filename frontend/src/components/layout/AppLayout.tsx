import { useState, type ReactNode } from 'react';
import dynamic from 'next/dynamic';

const Sidebar = dynamic(() => import('@/components/layout/Sidebar'), {
  ssr: false,
});

const Header = dynamic(() => import('@/components/layout/Header'), {
  ssr: false,
});

interface AppLayoutProps {
  children: ReactNode;
  scrollMain?: boolean;
}

export default function AppLayout({ children, scrollMain = true }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app flex h-full min-h-0 overflow-hidden bg-slate-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="layout flex h-full min-h-0 min-w-0 flex-1 flex-col lg:pl-64">
        <Header onOpenSidebar={() => setSidebarOpen(true)} />
        <main className={`main flex min-h-0 flex-1 flex-col overflow-x-hidden ${scrollMain ? 'overflow-y-auto' : 'overflow-hidden'}`}>
          {children}
        </main>
      </div>
    </div>
  );
}
