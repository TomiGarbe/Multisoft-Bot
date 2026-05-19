'use client';

import { Check, ChevronDown, Pipette } from 'lucide-react';
import { useEffect, useId, useMemo, useRef, useState } from 'react';

interface ColorPickerProps {
  label?: string;
  value: string;
  onChange: (next: string) => void;
  disabled?: boolean;
}

const PRESET_COLORS: { value: string; name: string }[] = [
  { value: '#0EA5E9', name: 'Sky' },
  { value: '#2563EB', name: 'Blue' },
  { value: '#6366F1', name: 'Indigo' },
  { value: '#7C3AED', name: 'Violet' },
  { value: '#A855F7', name: 'Purple' },
  { value: '#DB2777', name: 'Pink' },
  { value: '#E11D48', name: 'Rose' },
  { value: '#EF4444', name: 'Red' },
  { value: '#F97316', name: 'Orange' },
  { value: '#F59E0B', name: 'Amber' },
  { value: '#EAB308', name: 'Yellow' },
  { value: '#84CC16', name: 'Lime' },
  { value: '#22C55E', name: 'Green' },
  { value: '#10B981', name: 'Emerald' },
  { value: '#14B8A6', name: 'Teal' },
  { value: '#06B6D4', name: 'Cyan' },
  { value: '#475569', name: 'Slate' },
  { value: '#0F172A', name: 'Ink' },
];

function normalizeHex(input: string): string {
  const sanitized = input.trim().replace(/^#/, '').slice(0, 6);
  if (!sanitized) return '#2563EB';
  return `#${sanitized.padEnd(6, '0').toUpperCase()}`;
}

function isValidHex(input: string): boolean {
  return /^#[0-9A-Fa-f]{6}$/.test(input);
}

export default function ColorPicker({ label = 'Color', value, onChange, disabled = false }: ColorPickerProps) {
  const reactId = useId();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [open, setOpen] = useState(false);
  const normalized = useMemo(() => normalizeHex(value), [value]);
  const [draft, setDraft] = useState(normalized);
  const nativeInputId = `native-color-${reactId}`;

  useEffect(() => {
    setDraft(normalized);
  }, [normalized]);

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const commit = (next: string) => {
    const final = normalizeHex(next);
    setDraft(final);
    onChange(final);
  };

  return (
    <div className="space-y-1.5" ref={containerRef}>
      {label ? <label className="block text-sm font-medium text-slate-700">{label}</label> : null}

      <div className="relative">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen((v) => !v)}
          className={`flex h-10 w-full items-center gap-2 rounded-xl border bg-white px-2.5 text-left outline-none transition-all duration-150 disabled:cursor-not-allowed disabled:bg-slate-50 ${
            open
              ? 'border-sky-500 ring-2 ring-sky-200'
              : 'border-slate-300 hover:border-slate-400 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-200'
          }`}
        >
          <span
            aria-hidden
            className="relative h-7 w-7 shrink-0 overflow-hidden rounded-lg ring-1 ring-inset ring-slate-300"
            style={{ backgroundColor: normalized }}
          >
            <span
              className="absolute inset-0"
              style={{
                background:
                  'linear-gradient(135deg, rgba(255,255,255,0.35) 0%, rgba(255,255,255,0) 60%)',
              }}
            />
          </span>
          <span className="flex-1 font-mono text-xs font-semibold text-slate-700">{normalized}</span>
          <ChevronDown
            className={`h-4 w-4 shrink-0 text-slate-400 transition-transform duration-150 ${
              open ? 'rotate-180 text-sky-500' : ''
            }`}
          />
        </button>

        {open ? (
          <div className="animate-popover absolute left-0 right-0 z-50 mt-2 w-full min-w-[260px] rounded-xl border border-slate-200 bg-white p-3 shadow-lg ring-1 ring-black/5">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
              Paleta
            </p>
            <div className="grid grid-cols-6 gap-1.5">
              {PRESET_COLORS.map((preset) => {
                const isActive = preset.value === normalized;
                return (
                  <button
                    key={preset.value}
                    type="button"
                    title={`${preset.name} (${preset.value})`}
                    onClick={() => commit(preset.value)}
                    className={`group/swatch relative flex h-8 w-full items-center justify-center rounded-lg transition-all duration-150 hover:scale-105 ${
                      isActive ? 'ring-2 ring-offset-2 ring-sky-400' : 'ring-1 ring-slate-200'
                    }`}
                    style={{ backgroundColor: preset.value }}
                  >
                    {isActive ? (
                      <Check className="h-3.5 w-3.5 text-white drop-shadow-[0_1px_1px_rgba(0,0,0,0.35)]" strokeWidth={3} />
                    ) : null}
                  </button>
                );
              })}
            </div>

            <div className="mt-3 border-t border-slate-100 pt-3">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Personalizado
              </p>
              <div className="flex items-center gap-2">
                <label
                  htmlFor={nativeInputId}
                  className="relative inline-flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-lg ring-1 ring-inset ring-slate-300 transition-shadow hover:ring-slate-400"
                  style={{ backgroundColor: normalized }}
                >
                  <Pipette className="h-3.5 w-3.5 text-white/95 drop-shadow-[0_1px_1px_rgba(0,0,0,0.45)]" />
                  <input
                    id={nativeInputId}
                    type="color"
                    value={normalized}
                    disabled={disabled}
                    onChange={(event) => commit(event.target.value)}
                    className="pointer-events-none absolute inset-0 h-full w-full opacity-0"
                    tabIndex={-1}
                    aria-hidden
                  />
                </label>
                <div className="relative flex-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-slate-400">
                    #
                  </span>
                  <input
                    value={draft.replace(/^#/, '')}
                    onChange={(event) => setDraft(`#${event.target.value.replace(/^#/, '').slice(0, 6).toUpperCase()}`)}
                    onBlur={() => {
                      if (isValidHex(draft)) commit(draft);
                      else setDraft(normalized);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        event.currentTarget.blur();
                      }
                    }}
                    disabled={disabled}
                    className="h-9 w-full rounded-lg border border-slate-300 bg-white pl-7 pr-2 font-mono text-xs uppercase tracking-wider text-slate-700 outline-none transition-all duration-150 hover:border-slate-400 focus:border-sky-500 focus:ring-2 focus:ring-sky-200"
                    spellCheck={false}
                    maxLength={6}
                  />
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
