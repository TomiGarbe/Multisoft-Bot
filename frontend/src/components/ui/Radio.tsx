'use client';

import { forwardRef, useId, type InputHTMLAttributes } from 'react';

type RadioVariant = 'inline' | 'card';

interface RadioProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: string;
  description?: string;
  variant?: RadioVariant;
}

const Radio = forwardRef<HTMLInputElement, RadioProps>(function Radio(
  { label, description, variant = 'inline', className = '', id, checked, disabled, ...props },
  ref,
) {
  const reactId = useId();
  const inputId = id || `rd-${reactId}`;

  const visual = (
    <span
      aria-hidden
      className={`relative inline-flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full border transition-all duration-150 ${
        checked
          ? 'border-sky-600 bg-white shadow-sm'
          : 'border-slate-300 bg-white group-hover:border-slate-400'
      } ${disabled ? 'opacity-50' : ''} peer-focus-visible:ring-2 peer-focus-visible:ring-sky-200 peer-focus-visible:ring-offset-2`}
    >
      <span
        className={`block h-2 w-2 rounded-full transition-all duration-150 ${
          checked ? 'scale-100 bg-sky-600' : 'scale-0 bg-transparent'
        }`}
      />
    </span>
  );

  if (variant === 'card') {
    return (
      <label
        htmlFor={inputId}
        className={`group relative flex cursor-pointer items-start gap-3 rounded-xl border bg-white p-3 transition-all duration-150 hover:border-slate-300 hover:bg-slate-50/60 ${
          checked ? 'border-sky-300 bg-sky-50/40 ring-1 ring-sky-200' : 'border-slate-200'
        } ${disabled ? 'cursor-not-allowed opacity-60' : ''} ${className}`.trim()}
      >
        <input
          ref={ref}
          id={inputId}
          type="radio"
          className="peer sr-only"
          checked={checked}
          disabled={disabled}
          {...props}
        />
        {visual}
        <span className="min-w-0 flex-1">
          {label ? <span className="block text-sm font-medium text-slate-800">{label}</span> : null}
          {description ? (
            <span className="mt-0.5 block text-xs text-slate-500">{description}</span>
          ) : null}
        </span>
      </label>
    );
  }

  return (
    <label
      htmlFor={inputId}
      className={`group inline-flex cursor-pointer items-center gap-2.5 text-sm ${
        disabled ? 'cursor-not-allowed opacity-60' : ''
      } ${className}`.trim()}
    >
      <input
        ref={ref}
        id={inputId}
        type="radio"
        className="peer sr-only"
        checked={checked}
        disabled={disabled}
        {...props}
      />
      {visual}
      {label ? <span className="font-medium text-slate-700">{label}</span> : null}
    </label>
  );
});

export default Radio;
