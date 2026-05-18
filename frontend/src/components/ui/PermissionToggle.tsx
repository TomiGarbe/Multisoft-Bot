'use client';

import type { ReactNode } from 'react';
import Switch from '@/components/ui/Switch';

interface PermissionToggleProps {
  label: string;
  description?: ReactNode;
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  icon?: ReactNode;
}

export default function PermissionToggle({
  label,
  description,
  checked,
  onChange,
  disabled,
  icon,
}: PermissionToggleProps) {
  return (
    <label
      className={`group relative flex cursor-pointer items-center gap-3 rounded-xl border bg-white p-3 transition-all duration-150 hover:border-slate-300 hover:bg-slate-50/60 ${
        checked ? 'border-sky-300 bg-sky-50/40' : 'border-slate-200'
      } ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}
    >
      {icon ? (
        <span
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors ${
            checked ? 'bg-sky-100 text-sky-600' : 'bg-slate-100 text-slate-500'
          }`}
        >
          {icon}
        </span>
      ) : null}
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium text-slate-800">{label}</span>
        {description ? (
          <span className="mt-0.5 block truncate text-xs text-slate-500">{description}</span>
        ) : null}
      </span>
      <Switch
        size="sm"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        disabled={disabled}
        aria-label={label}
      />
    </label>
  );
}
