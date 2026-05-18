'use client';

import type { ReactNode } from 'react';

interface FormFieldProps {
  label?: ReactNode;
  htmlFor?: string;
  hint?: ReactNode;
  error?: ReactNode;
  required?: boolean;
  optional?: boolean;
  children: ReactNode;
}

export default function FormField({
  label,
  htmlFor,
  hint,
  error,
  required,
  optional,
  children,
}: FormFieldProps) {
  return (
    <div className="space-y-1.5">
      {label ? (
        <label
          htmlFor={htmlFor}
          className="flex items-center justify-between gap-2 text-sm font-medium text-slate-700"
        >
          <span>
            {label}
            {required ? <span className="ml-0.5 text-rose-500">*</span> : null}
          </span>
          {optional ? <span className="text-xs font-normal text-slate-400">Opcional</span> : null}
        </label>
      ) : null}
      {children}
      {error ? (
        <p className="text-xs font-medium text-rose-600">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
}
