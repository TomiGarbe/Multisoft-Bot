'use client';

import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  children: ReactNode;
}

export default function Button({ variant = 'primary', className = '', children, ...props }: ButtonProps) {
  const baseStyles =
    'inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60';

  const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
    primary: 'bg-sky-600 text-white hover:bg-sky-700',
    secondary: 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50',
    danger: 'bg-rose-600 text-white hover:bg-rose-700',
    ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
  };

  return (
    <button className={`${baseStyles} ${variants[variant]} ${className}`.trim()} {...props}>
      {children}
    </button>
  );
}
