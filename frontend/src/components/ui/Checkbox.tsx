'use client';

import type { InputHTMLAttributes } from 'react';

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
  description?: string;
}

export default function Checkbox({ label, description, className = '', id, ...props }: CheckboxProps) {
  const checkboxId = id || label.toLowerCase().replace(/\s+/g, '-');

  return (
    <label
      htmlFor={checkboxId}
      className={`flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 bg-white p-3 hover:bg-slate-50 ${className}`.trim()}
    >
      <input
        id={checkboxId}
        type="checkbox"
        className="mt-0.5 h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
        {...props}
      />
      <span>
        <span className="block text-sm font-medium text-slate-800">{label}</span>
        {description ? <span className="block text-xs text-slate-500">{description}</span> : null}
      </span>
    </label>
  );
}
