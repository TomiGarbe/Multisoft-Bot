'use client';

import type { ReactNode } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:pl-64">
        <Header />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
