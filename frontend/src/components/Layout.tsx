'use client';

interface LayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
}

export default function Layout({ children, sidebar }: LayoutProps) {
  return (
    <div className="flex min-h-screen">
      {sidebar && <>{sidebar}</>}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}
