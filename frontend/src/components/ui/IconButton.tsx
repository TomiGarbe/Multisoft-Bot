'use client';

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';

type IconButtonVariant = 'default' | 'primary' | 'danger' | 'ghost' | 'subtle';
type IconButtonSize = 'sm' | 'md' | 'lg';

interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  icon: ReactNode;
  label: string;
  variant?: IconButtonVariant;
  size?: IconButtonSize;
  tone?: 'neutral' | 'destructive' | 'success' | 'info';
}

const SIZE_STYLES: Record<IconButtonSize, string> = {
  sm: 'h-7 w-7 [&_svg]:h-3.5 [&_svg]:w-3.5',
  md: 'h-9 w-9 [&_svg]:h-4 [&_svg]:w-4',
  lg: 'h-10 w-10 [&_svg]:h-5 [&_svg]:w-5',
};

const VARIANT_STYLES: Record<IconButtonVariant, string> = {
  default:
    'border border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 active:scale-95 focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2',
  primary:
    'border border-sky-600 bg-sky-600 text-white hover:bg-sky-700 active:scale-95 focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2',
  danger:
    'border border-rose-200 bg-white text-rose-600 hover:border-rose-300 hover:bg-rose-50 hover:text-rose-700 active:scale-95 focus-visible:ring-2 focus-visible:ring-rose-300 focus-visible:ring-offset-2',
  ghost:
    'text-slate-500 hover:bg-slate-100 hover:text-slate-900 active:scale-95 focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2',
  subtle:
    'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900 active:scale-95 focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-2',
};

const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { icon, label, variant = 'default', size = 'md', className = '', type = 'button', ...props },
  ref,
) {
  const base =
    'inline-flex items-center justify-center rounded-lg outline-none transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100';

  return (
    <button
      ref={ref}
      type={type}
      aria-label={label}
      title={label}
      className={`${base} ${SIZE_STYLES[size]} ${VARIANT_STYLES[variant]} ${className}`.trim()}
      {...props}
    >
      {icon}
    </button>
  );
});

export default IconButton;
