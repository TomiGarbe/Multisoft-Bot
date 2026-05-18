'use client';

import { Check, ChevronDown, X } from 'lucide-react';
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from 'react';

export interface MultiSelectOption {
  value: string;
  label: string;
  description?: string;
  icon?: ReactNode;
}

interface MultiSelectProps {
  label?: string;
  options: MultiSelectOption[];
  value: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
  hint?: string;
  error?: string;
  disabled?: boolean;
  maxChips?: number;
}

export default function MultiSelect({
  label,
  options,
  value,
  onChange,
  placeholder = 'Selecciona opciones',
  hint,
  error,
  disabled = false,
  maxChips = 3,
}: MultiSelectProps) {
  const reactId = useId();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedSet = useMemo(() => new Set(value), [value]);

  const filteredOptions = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return options;
    return options.filter((option) => option.label.toLowerCase().includes(q));
  }, [options, search]);

  const selectedOptions = useMemo(
    () => options.filter((option) => selectedSet.has(option.value)),
    [options, selectedSet],
  );

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
        setSearch('');
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const toggle = (optionValue: string) => {
    if (selectedSet.has(optionValue)) {
      onChange(value.filter((id) => id !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  const remove = (optionValue: string) => {
    onChange(value.filter((id) => id !== optionValue));
  };

  const visibleChips = selectedOptions.slice(0, maxChips);
  const overflow = selectedOptions.length - visibleChips.length;

  return (
    <div className="space-y-1.5" ref={containerRef}>
      {label ? (
        <label htmlFor={reactId} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      ) : null}

      <div className="relative">
        <button
          id={reactId}
          type="button"
          disabled={disabled}
          onClick={() => setOpen((v) => !v)}
          className={`flex min-h-10 w-full items-center gap-2 rounded-xl border bg-white px-3 py-1.5 text-left text-sm outline-none transition-all duration-150 disabled:cursor-not-allowed disabled:bg-slate-50 ${
            error
              ? 'border-rose-400 hover:border-rose-500'
              : open
                ? 'border-sky-500 ring-2 ring-sky-200'
                : 'border-slate-300 hover:border-slate-400'
          }`}
        >
          <div className="flex flex-1 flex-wrap items-center gap-1.5">
            {selectedOptions.length === 0 ? (
              <span className="text-slate-400">{placeholder}</span>
            ) : (
              <>
                {visibleChips.map((option) => (
                  <span
                    key={option.value}
                    className="inline-flex items-center gap-1 rounded-md bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-700 ring-1 ring-inset ring-sky-200"
                  >
                    {option.icon ? (
                      <span className="inline-flex shrink-0 items-center">{option.icon}</span>
                    ) : null}
                    {option.label}
                    <span
                      role="button"
                      tabIndex={-1}
                      aria-label={`Quitar ${option.label}`}
                      className="rounded hover:bg-sky-100 hover:text-sky-900"
                      onClick={(e) => {
                        e.stopPropagation();
                        remove(option.value);
                      }}
                    >
                      <X className="h-3 w-3" />
                    </span>
                  </span>
                ))}
                {overflow > 0 ? (
                  <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                    +{overflow}
                  </span>
                ) : null}
              </>
            )}
          </div>
          <ChevronDown
            className={`h-4 w-4 shrink-0 text-slate-400 transition-transform duration-150 ${
              open ? 'rotate-180 text-sky-500' : ''
            }`}
          />
        </button>

        {open ? (
          <div className="animate-popover absolute z-50 mt-2 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg ring-1 ring-black/5">
            <div className="border-b border-slate-100 p-2">
              <input
                autoFocus
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar..."
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-sm outline-none placeholder:text-slate-400 focus:border-sky-400 focus:bg-white"
              />
            </div>
            <ul className="max-h-60 overflow-y-auto py-1" role="listbox">
              {filteredOptions.length === 0 ? (
                <li className="px-3 py-6 text-center text-xs text-slate-500">Sin resultados</li>
              ) : (
                filteredOptions.map((option) => {
                  const checked = selectedSet.has(option.value);
                  return (
                    <li key={option.value}>
                      <button
                        type="button"
                        onClick={() => toggle(option.value)}
                        className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors ${
                          checked ? 'bg-sky-50/60 text-sky-900' : 'text-slate-700 hover:bg-slate-50'
                        }`}
                        role="option"
                        aria-selected={checked}
                      >
                        <span
                          className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-all duration-150 ${
                            checked
                              ? 'border-sky-600 bg-sky-600 text-white'
                              : 'border-slate-300 bg-white group-hover:border-slate-400'
                          }`}
                        >
                          {checked ? <Check className="h-3 w-3" strokeWidth={3} /> : null}
                        </span>
                        {option.icon ? (
                          <span className="inline-flex shrink-0 items-center">{option.icon}</span>
                        ) : null}
                        <span className="flex-1 truncate">
                          <span className="font-medium">{option.label}</span>
                          {option.description ? (
                            <span className="ml-1 text-xs text-slate-500">{option.description}</span>
                          ) : null}
                        </span>
                      </button>
                    </li>
                  );
                })
              )}
            </ul>
          </div>
        ) : null}
      </div>

      {error ? (
        <p className="text-xs font-medium text-rose-600">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
}
