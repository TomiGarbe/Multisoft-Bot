'use client';

import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  warning?: string;
  hint?: string;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, id, error, warning, hint, leadingIcon, trailingIcon, className = '', disabled, ...props },
  ref,
) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  const state = error ? 'error' : warning ? 'warning' : 'default';
  const stateStyles = {
    default:
      'border-slate-300 hover:border-slate-400 focus-visible:border-sky-500 focus-visible:ring-sky-200',
    error:
      'border-rose-400 hover:border-rose-500 focus-visible:border-rose-500 focus-visible:ring-rose-200',
    warning:
      'border-amber-300 bg-amber-50/40 hover:border-amber-400 focus-visible:border-amber-500 focus-visible:ring-amber-200',
  } as const;

  return (
    <div className="space-y-1.5">
      {label ? (
        <label htmlFor={inputId} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      ) : null}
      <div className="relative">
        {leadingIcon ? (
          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400 [&_svg]:h-4 [&_svg]:w-4">
            {leadingIcon}
          </span>
        ) : null}
        <input
          ref={ref}
          id={inputId}
          disabled={disabled}
          className={`h-10 w-full rounded-xl border bg-white text-sm text-slate-900 outline-none transition-all duration-150 placeholder:text-slate-400 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 ${
            leadingIcon ? 'pl-9' : 'pl-3.5'
          } ${trailingIcon ? 'pr-9' : 'pr-3.5'} focus-visible:ring-2 ${stateStyles[state]} ${className}`.trim()}
          {...props}
        />
        {trailingIcon ? (
          <span className="absolute inset-y-0 right-3 flex items-center text-slate-400 [&_svg]:h-4 [&_svg]:w-4">
            {trailingIcon}
          </span>
        ) : null}
      </div>
      {error ? (
        <p className="text-xs font-medium text-rose-600">{error}</p>
      ) : warning ? (
        <p className="text-xs font-medium text-amber-700">{warning}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
});

export default Input;
