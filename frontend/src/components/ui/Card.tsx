'use client';

import type { ReactNode } from 'react';

interface CardProps {
  title?: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  actions?: ReactNode;
  icon?: ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg' | 'none';
  hover?: boolean;
}

const PADDING = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
};

export default function Card({
  title,
  description,
  children,
  actions,
  icon,
  className = '',
  padding = 'md',
  hover = false,
}: CardProps) {
  return (
    <section
      className={`rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-200 ${
        hover ? 'hover:shadow-md hover:-translate-y-px' : ''
      } ${PADDING[padding]} ${className}`.trim()}
    >
      {title || actions ? (
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            {icon ? (
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-sky-50 text-sky-600 ring-1 ring-inset ring-sky-100">
                {icon}
              </span>
            ) : null}
            <div className="min-w-0">
              {title ? <h3 className="text-base font-semibold text-slate-900">{title}</h3> : null}
              {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
            </div>
          </div>
          {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
