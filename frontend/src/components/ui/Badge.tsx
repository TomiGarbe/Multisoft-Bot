'use client';

import type { ReactNode } from 'react';

type BadgeTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'accent';
type BadgeVariant = 'soft' | 'outline' | 'solid' | 'dot';
type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  label: ReactNode;
  tone?: BadgeTone;
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: ReactNode;
  className?: string;
}

const SOFT: Record<BadgeTone, string> = {
  neutral: 'bg-slate-100 text-slate-700 ring-slate-200',
  info: 'bg-sky-50 text-sky-700 ring-sky-200',
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  warning: 'bg-amber-50 text-amber-800 ring-amber-200',
  danger: 'bg-rose-50 text-rose-700 ring-rose-200',
  accent: 'bg-violet-50 text-violet-700 ring-violet-200',
};

const OUTLINE: Record<BadgeTone, string> = {
  neutral: 'border-slate-200 bg-white text-slate-700',
  info: 'border-sky-200 bg-white text-sky-700',
  success: 'border-emerald-200 bg-white text-emerald-700',
  warning: 'border-amber-200 bg-white text-amber-800',
  danger: 'border-rose-200 bg-white text-rose-700',
  accent: 'border-violet-200 bg-white text-violet-700',
};

const SOLID: Record<BadgeTone, string> = {
  neutral: 'bg-slate-700 text-white',
  info: 'bg-sky-600 text-white',
  success: 'bg-emerald-600 text-white',
  warning: 'bg-amber-500 text-white',
  danger: 'bg-rose-600 text-white',
  accent: 'bg-violet-600 text-white',
};

const DOT_COLORS: Record<BadgeTone, string> = {
  neutral: 'bg-slate-400',
  info: 'bg-sky-500',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-rose-500',
  accent: 'bg-violet-500',
};

const SIZE: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-[11px]',
  md: 'px-2.5 py-1 text-xs',
};

export default function Badge({
  label,
  tone = 'neutral',
  variant = 'soft',
  size = 'md',
  icon,
  className = '',
}: BadgeProps) {
  if (variant === 'dot') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 rounded-full bg-slate-50 ring-1 ring-inset ring-slate-200 ${SIZE[size]} font-medium text-slate-700 ${className}`.trim()}
      >
        <span className={`h-1.5 w-1.5 rounded-full ${DOT_COLORS[tone]}`} />
        {label}
      </span>
    );
  }

  const styles =
    variant === 'outline'
      ? `border ${OUTLINE[tone]}`
      : variant === 'solid'
        ? SOLID[tone]
        : `ring-1 ring-inset ${SOFT[tone]}`;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-semibold ${styles} ${SIZE[size]} ${className}`.trim()}
    >
      {icon ? <span className="inline-flex [&_svg]:h-3 [&_svg]:w-3">{icon}</span> : null}
      {label}
    </span>
  );
}
