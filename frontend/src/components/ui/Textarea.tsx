'use client';

import { forwardRef, type TextareaHTMLAttributes } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, id, error, hint, className = '', disabled, ...props },
  ref,
) {
  const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="space-y-1.5">
      {label ? (
        <label htmlFor={textareaId} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      ) : null}
      <textarea
        ref={ref}
        id={textareaId}
        disabled={disabled}
        className={`w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition-all duration-150 placeholder:text-slate-400 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 ${
          error
            ? 'border-rose-400 hover:border-rose-500 focus-visible:border-rose-500 focus-visible:ring-2 focus-visible:ring-rose-200'
            : 'border-slate-300 hover:border-slate-400 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-200'
        } ${className}`.trim()}
        {...props}
      />
      {error ? (
        <p className="text-xs font-medium text-rose-600">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
});

export default Textarea;
