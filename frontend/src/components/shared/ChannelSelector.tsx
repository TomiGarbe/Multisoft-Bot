import type { ReactNode } from 'react';

export interface ChannelSelectorOption {
  value: string;
  label: string;
}

interface ChannelSelectorProps {
  label?: ReactNode;
  value: string;
  options: ChannelSelectorOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export default function ChannelSelector({
  label = 'Canal',
  value,
  options,
  onChange,
  disabled,
  placeholder = 'Seleccionar canal',
  className = '',
}: ChannelSelectorProps) {
  return (
    <div className={`space-y-1.5 ${className}`.trim()}>
      {label ? <label className="block text-sm font-medium text-slate-700">{label}</label> : null}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {!options.length ? <option value="">{placeholder}</option> : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
