'use client';

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'destructive';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  loading?: boolean;
  children?: ReactNode;
}

const VARIANT_STYLES: Record<ButtonVariant, string> = {
  primary:
    'bg-sky-600 text-white shadow-sm hover:bg-sky-700 active:bg-sky-800 focus-visible:ring-sky-300 disabled:hover:bg-sky-600',
  secondary:
    'border border-slate-300 bg-white text-slate-700 shadow-sm hover:border-slate-400 hover:bg-slate-50 hover:text-slate-900 active:bg-slate-100 focus-visible:ring-slate-300',
  danger:
    'bg-rose-600 text-white shadow-sm hover:bg-rose-700 active:bg-rose-800 focus-visible:ring-rose-300 disabled:hover:bg-rose-600',
  destructive:
    'border border-rose-200 bg-white text-rose-600 shadow-sm hover:border-rose-300 hover:bg-rose-50 hover:text-rose-700 active:bg-rose-100 focus-visible:ring-rose-300',
  ghost:
    'text-slate-600 hover:bg-slate-100 hover:text-slate-900 active:bg-slate-200 focus-visible:ring-slate-300',
};

const SIZE_STYLES: Record<ButtonSize, string> = {
  sm: 'h-8 gap-1.5 px-3 text-xs',
  md: 'h-10 gap-2 px-4 text-sm',
  lg: 'h-11 gap-2 px-5 text-sm',
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = 'primary',
    size = 'md',
    className = '',
    leadingIcon,
    trailingIcon,
    loading = false,
    disabled,
    children,
    ...props
  },
  ref,
) {
  const baseStyles =
    'group/btn relative inline-flex items-center justify-center rounded-xl font-semibold outline-none transition-all duration-150 active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100';

  const isDisabled = disabled || loading;

  return (
    <button
      ref={ref}
      disabled={isDisabled}
      className={`${baseStyles} ${VARIANT_STYLES[variant]} ${SIZE_STYLES[size]} ${className}`.trim()}
      {...props}
    >
      {loading ? (
        <span
          aria-hidden
          className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent opacity-80"
        />
      ) : leadingIcon ? (
        <span className="inline-flex shrink-0 items-center [&_svg]:h-4 [&_svg]:w-4">{leadingIcon}</span>
      ) : null}
      {children ? <span className="inline-flex items-center">{children}</span> : null}
      {!loading && trailingIcon ? (
        <span className="inline-flex shrink-0 items-center [&_svg]:h-4 [&_svg]:w-4">{trailingIcon}</span>
      ) : null}
    </button>
  );
});

export default Button;
