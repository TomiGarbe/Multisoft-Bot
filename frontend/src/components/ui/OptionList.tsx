'use client';

import { Check } from 'lucide-react';
import type { ReactNode } from 'react';

export interface OptionListItem<T extends string = string> {
  value: T;
  label: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  trailing?: ReactNode;
  disabled?: boolean;
}

interface OptionListProps<T extends string = string> {
  options: OptionListItem<T>[];
  value: T | null;
  onChange: (value: T) => void;
  label?: string;
  multi?: false;
  size?: 'sm' | 'md';
}

interface MultiOptionListProps<T extends string = string> {
  options: OptionListItem<T>[];
  value: T[];
  onChange: (value: T[]) => void;
  label?: string;
  multi: true;
  size?: 'sm' | 'md';
}

type Props<T extends string = string> = OptionListProps<T> | MultiOptionListProps<T>;

export default function OptionList<T extends string = string>(props: Props<T>) {
  const { options, label, size = 'md' } = props;

  const isSelected = (item: OptionListItem<T>) =>
    props.multi ? props.value.includes(item.value) : props.value === item.value;

  const handleSelect = (item: OptionListItem<T>) => {
    if (item.disabled) return;
    if (props.multi) {
      const has = props.value.includes(item.value);
      props.onChange(
        has ? props.value.filter((v) => v !== item.value) : [...props.value, item.value],
      );
    } else {
      props.onChange(item.value);
    }
  };

  const padding = size === 'sm' ? 'px-3 py-2' : 'px-3.5 py-2.5';

  return (
    <div className="space-y-1.5">
      {label ? <p className="text-sm font-medium text-slate-700">{label}</p> : null}
      <ul className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {options.map((item, index) => {
          const selected = isSelected(item);
          return (
            <li key={item.value} className={index > 0 ? 'border-t border-slate-100' : ''}>
              <button
                type="button"
                disabled={item.disabled}
                onClick={() => handleSelect(item)}
                className={`group/option relative flex w-full items-center gap-3 ${padding} text-left text-sm transition-all duration-150 ${
                  selected
                    ? 'bg-sky-50/70 text-sky-900'
                    : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
                } ${item.disabled ? 'cursor-not-allowed opacity-50' : ''}`}
              >
                {selected ? (
                  <span
                    aria-hidden
                    className="absolute inset-y-0 left-0 w-0.5 bg-sky-500"
                  />
                ) : null}
                {item.icon ? (
                  <span
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors ${
                      selected
                        ? 'bg-sky-100 text-sky-600'
                        : 'bg-slate-100 text-slate-500 group-hover/option:bg-slate-200'
                    }`}
                  >
                    {item.icon}
                  </span>
                ) : null}
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{item.label}</span>
                  {item.description ? (
                    <span className="mt-0.5 block truncate text-xs text-slate-500">
                      {item.description}
                    </span>
                  ) : null}
                </span>
                {item.trailing ? (
                  <span className="shrink-0 text-xs text-slate-500">{item.trailing}</span>
                ) : null}
                {selected ? (
                  <Check className="h-4 w-4 shrink-0 text-sky-600" strokeWidth={3} />
                ) : null}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
