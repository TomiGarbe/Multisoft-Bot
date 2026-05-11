import type { ReactNode } from 'react';

interface ChartCardProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export default function ChartCard({ title, description, children }: ChartCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white px-5 py-5 shadow-sm sm:px-6 sm:py-6">
      <h3 className="text-base font-semibold text-slate-900 sm:text-lg">{title}</h3>
      {description ? <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p> : null}
      <div className="mt-4 sm:mt-5">{children}</div>
    </article>
  );
}
