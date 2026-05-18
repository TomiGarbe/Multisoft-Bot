import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  icon?: ReactNode;
  breadcrumb?: ReactNode;
}

export default function PageHeader({ title, description, actions, icon, breadcrumb }: PageHeaderProps) {
  return (
    <section className="flex flex-col items-start justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-center md:p-6">
      <div className="flex min-w-0 items-center gap-4">
        {icon ? (
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-50 text-sky-600 ring-1 ring-inset ring-sky-100">
            {icon}
          </span>
        ) : null}
        <div className="min-w-0">
          {breadcrumb ? <div className="mb-1 text-xs text-slate-500">{breadcrumb}</div> : null}
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 md:text-[28px]">{title}</h1>
          {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </section>
  );
}
