'use client';

import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from 'react';

type SwitchSize = 'sm' | 'md';
type SwitchLayout = 'between' | 'inline';

interface SwitchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: ReactNode;
  description?: ReactNode;
  size?: SwitchSize;
  layout?: SwitchLayout;
}

const TRACK_SIZE: Record<SwitchSize, string> = {
  sm: 'h-[18px] w-8',
  md: 'h-5 w-9',
};

const THUMB_SIZE: Record<SwitchSize, string> = {
  sm: 'h-3.5 w-3.5 translate-x-0.5 peer-checked:translate-x-[14px]',
  md: 'h-4 w-4 translate-x-0.5 peer-checked:translate-x-[18px]',
};

const Switch = forwardRef<HTMLInputElement, SwitchProps>(function Switch(
  {
    label,
    description,
    size = 'md',
    layout = 'between',
    checked,
    className = '',
    id,
    disabled,
    ...props
  },
  ref,
) {
  const reactId = useId();
  const switchId = id || `sw-${reactId}`;

  const control = (
    <span className={`relative inline-flex shrink-0 items-center ${TRACK_SIZE[size]}`}>
      <input
        ref={ref}
        id={switchId}
        type="checkbox"
        className="peer sr-only"
        checked={checked}
        disabled={disabled}
        {...props}
      />
      <span
        className={`absolute inset-0 rounded-full bg-slate-300 transition-colors duration-200 ease-out peer-checked:bg-sky-600 peer-focus-visible:ring-2 peer-focus-visible:ring-sky-200 peer-focus-visible:ring-offset-2 ${
          disabled ? 'opacity-50' : ''
        }`}
      />
      <span
        aria-hidden
        className={`absolute left-0 ${THUMB_SIZE[size]} rounded-full bg-white shadow-sm ring-1 ring-black/5 transition-transform duration-200 ease-out`}
      />
    </span>
  );

  if (!label) {
    return (
      <label
        htmlFor={switchId}
        className={`inline-flex cursor-pointer items-center ${
          disabled ? 'cursor-not-allowed opacity-60' : ''
        } ${className}`.trim()}
      >
        {control}
      </label>
    );
  }

  if (layout === 'inline') {
    return (
      <label
        htmlFor={switchId}
        className={`inline-flex cursor-pointer items-center gap-2.5 text-sm ${
          disabled ? 'cursor-not-allowed opacity-60' : ''
        } ${className}`.trim()}
      >
        {control}
        <span className="font-medium text-slate-700">{label}</span>
      </label>
    );
  }

  return (
    <label
      htmlFor={switchId}
      className={`flex cursor-pointer items-center justify-between gap-3 ${
        disabled ? 'cursor-not-allowed opacity-60' : ''
      } ${className}`.trim()}
    >
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium text-slate-800">{label}</span>
        {description ? (
          <span className="mt-0.5 block text-xs text-slate-500">{description}</span>
        ) : null}
      </span>
      {control}
    </label>
  );
});

export default Switch;
