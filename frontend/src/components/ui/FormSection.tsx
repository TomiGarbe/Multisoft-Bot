'use client';

import type { ReactNode } from 'react';

interface FormSectionProps {
  title: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  variant?: 'soft' | 'bare';
}

export default function FormSection({
  title,
  description,
  icon,
  actions,
  children,
  variant = 'soft',
}: FormSectionProps) {
  const wrapper =
    variant === 'soft'
      ? 'rounded-2xl border border-slate-200 bg-slate-50/40 p-4 md:p-5'
      : 'space-y-3';

  return (
    <section className={`space-y-3 ${wrapper}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          {icon ? (
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-sky-600 ring-1 ring-inset ring-slate-200">
              {icon}
            </span>
          ) : null}
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
            {description ? <p className="mt-0.5 text-xs text-slate-500">{description}</p> : null}
          </div>
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
      <div>{children}</div>
    </section>
  );
}
