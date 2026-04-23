'use client';

import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export default function Input({ label, id, error, className = '', ...props }: InputProps) {
  const inputId = id || label.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="space-y-1.5">
      <label htmlFor={inputId} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        className={`w-full rounded-lg border px-3 py-2 text-sm text-slate-900 outline-none transition focus:ring-2 focus:ring-sky-200 ${
          error ? 'border-rose-400 focus:border-rose-400' : 'border-slate-300 focus:border-sky-400'
        } ${className}`.trim()}
        {...props}
      />
      {error ? <p className="text-xs text-rose-600">{error}</p> : null}
    </div>
  );
}
