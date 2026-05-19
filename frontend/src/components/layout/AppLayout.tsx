import { useEffect, useState, type ReactNode } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';

interface AppLayoutProps {
  children: ReactNode;
  scrollMain?: boolean;
}

export default function AppLayout({ children, scrollMain = true }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const hydrationDebugEnabled = process.env.NEXT_PUBLIC_DEBUG_HYDRATION === '1';

  useEffect(() => {
    if (!hydrationDebugEnabled) return;
    console.info('[HYDRATION] client mounted app layout');
  }, [hydrationDebugEnabled]);

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
