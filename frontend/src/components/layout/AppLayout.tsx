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
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app flex min-h-screen bg-slate-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="layout flex min-h-screen min-w-0 flex-1 flex-col lg:pl-64">
        <Header onOpenSidebar={() => setSidebarOpen(true)} />
        <main className="main flex min-h-0 flex-1 flex-col overflow-y-auto overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
}
