import type { ReactNode } from 'react';

interface StatCardProps {
  title: ReactNode;
  value: ReactNode;
  subtitle?: ReactNode;
  icon?: ReactNode;
  trend?: { value: string; positive?: boolean };
}

export default function StatCard({ title, value, subtitle, icon, trend }: StatCardProps) {
  return (
    <article className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-px hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        {icon ? (
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-50 text-sky-600 ring-1 ring-inset ring-sky-100">
            {icon}
          </span>
        ) : null}
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
      {trend || subtitle ? (
        <div className="mt-2 flex items-center gap-2 text-sm">
          {trend ? (
            <span
              className={`inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs font-semibold ${
                trend.positive
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-rose-50 text-rose-700'
              }`}
            >
              {trend.value}
            </span>
          ) : null}
          {subtitle ? <p className="text-sm text-slate-500">{subtitle}</p> : null}
        </div>
      ) : null}
    </article>
  );
}
