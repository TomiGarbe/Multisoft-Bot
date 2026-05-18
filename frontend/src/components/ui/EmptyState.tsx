'use client';

import { Inbox } from 'lucide-react';
import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  compact?: boolean;
}

export default function EmptyState({
  title,
  description,
  icon,
  action,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 px-4 text-center ${
        compact ? 'py-6' : 'py-12'
      }`}
    >
      <span
        className={`mb-3 inline-flex items-center justify-center rounded-full bg-white text-slate-400 ring-1 ring-slate-200 ${
          compact ? 'h-9 w-9 [&_svg]:h-4 [&_svg]:w-4' : 'h-12 w-12 [&_svg]:h-5 [&_svg]:w-5'
        }`}
      >
        {icon ?? <Inbox />}
      </span>
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      {description ? (
        <p className="mt-1 max-w-md text-sm text-slate-500">{description}</p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
