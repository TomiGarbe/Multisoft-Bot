'use client';

import { CalendarDays, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from 'react';

interface DatePickerProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  min?: string;
  max?: string;
  placeholder?: string;
  hint?: ReactNode;
  error?: string;
  disabled?: boolean;
  clearable?: boolean;
  id?: string;
}

const MONTH_NAMES = [
  'Enero',
  'Febrero',
  'Marzo',
  'Abril',
  'Mayo',
  'Junio',
  'Julio',
  'Agosto',
  'Septiembre',
  'Octubre',
  'Noviembre',
  'Diciembre',
];

const WEEKDAY_SHORT = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'];

function pad2(n: number): string {
  return String(n).padStart(2, '0');
}

function formatIso(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

function parseIso(value: string): Date | null {
  if (!value) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  const [, y, m, d] = match;
  const date = new Date(Number(y), Number(m) - 1, Number(d));
  return Number.isNaN(date.getTime()) ? null : date;
}

function stripTime(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function formatDisplay(date: Date): string {
  const day = pad2(date.getDate());
  const month = pad2(date.getMonth() + 1);
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

interface DayCell {
  date: Date;
  inMonth: boolean;
}

function buildMonthGrid(viewYear: number, viewMonth: number): DayCell[] {
  const firstOfMonth = new Date(viewYear, viewMonth, 1);
  const lastOfMonth = new Date(viewYear, viewMonth + 1, 0);
  // 0=Mon ... 6=Sun
  const firstWeekday = (firstOfMonth.getDay() + 6) % 7;
  const totalDays = lastOfMonth.getDate();

  const cells: DayCell[] = [];

  for (let i = firstWeekday; i > 0; i -= 1) {
    const date = new Date(viewYear, viewMonth, 1 - i);
    cells.push({ date, inMonth: false });
  }

  for (let day = 1; day <= totalDays; day += 1) {
    cells.push({ date: new Date(viewYear, viewMonth, day), inMonth: true });
  }

  const remainder = cells.length % 7;
  if (remainder !== 0) {
    const padding = 7 - remainder;
    for (let i = 1; i <= padding; i += 1) {
      cells.push({ date: new Date(viewYear, viewMonth + 1, i), inMonth: false });
    }
  }

  // Ensure 6 rows for visual stability
  while (cells.length < 42) {
    const last = cells[cells.length - 1].date;
    const next = new Date(last);
    next.setDate(last.getDate() + 1);
    cells.push({ date: next, inMonth: false });
  }

  return cells;
}

export default function DatePicker({
  label,
  value,
  onChange,
  min,
  max,
  placeholder = 'Selecciona una fecha',
  hint,
  error,
  disabled = false,
  clearable = true,
  id,
}: DatePickerProps) {
  const reactId = useId();
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : `dp-${reactId}`);

  const containerRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);

  const selectedDate = useMemo(() => parseIso(value), [value]);
  const minDate = useMemo(() => parseIso(min ?? ''), [min]);
  const maxDate = useMemo(() => parseIso(max ?? ''), [max]);
  const today = useMemo(() => stripTime(new Date()), []);

  const initialView = selectedDate ?? minDate ?? today;
  const [viewYear, setViewYear] = useState(initialView.getFullYear());
  const [viewMonth, setViewMonth] = useState(initialView.getMonth());

  useEffect(() => {
    if (selectedDate) {
      setViewYear(selectedDate.getFullYear());
      setViewMonth(selectedDate.getMonth());
    }
  }, [value, selectedDate]);

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const keyHandler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    document.addEventListener('keydown', keyHandler);
    return () => {
      document.removeEventListener('mousedown', handler);
      document.removeEventListener('keydown', keyHandler);
    };
  }, [open]);

  const cells = useMemo(() => buildMonthGrid(viewYear, viewMonth), [viewYear, viewMonth]);

  const isDisabledDay = (date: Date): boolean => {
    const day = stripTime(date);
    if (minDate && day < stripTime(minDate)) return true;
    if (maxDate && day > stripTime(maxDate)) return true;
    return false;
  };

  const goPrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear((y) => y - 1);
    } else {
      setViewMonth((m) => m - 1);
    }
  };

  const goNextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear((y) => y + 1);
    } else {
      setViewMonth((m) => m + 1);
    }
  };

  const pickDate = (date: Date) => {
    if (isDisabledDay(date)) return;
    onChange(formatIso(date));
    setOpen(false);
  };

  const clearValue = (event: React.MouseEvent) => {
    event.stopPropagation();
    onChange('');
  };

  const jumpToToday = () => {
    const todayDate = new Date();
    if (!isDisabledDay(todayDate)) {
      onChange(formatIso(todayDate));
      setOpen(false);
    } else {
      setViewYear(todayDate.getFullYear());
      setViewMonth(todayDate.getMonth());
    }
  };

  const monthLabel = `${MONTH_NAMES[viewMonth]} ${viewYear}`;

  return (
    <div className="space-y-1.5" ref={containerRef}>
      {label ? (
        <label htmlFor={inputId} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      ) : null}

      <div className="relative">
        <button
          id={inputId}
          type="button"
          disabled={disabled}
          onClick={() => setOpen((v) => !v)}
          aria-haspopup="dialog"
          aria-expanded={open}
          className={`group/dp flex h-10 w-full items-center gap-2 rounded-xl border bg-white pl-3.5 pr-2 text-left text-sm outline-none transition-all duration-150 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 ${
            error
              ? 'border-rose-400 hover:border-rose-500'
              : open
                ? 'border-sky-500 ring-2 ring-sky-200'
                : 'border-slate-300 hover:border-slate-400 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-200'
          }`}
        >
          <CalendarDays className="h-4 w-4 shrink-0 text-slate-400 group-hover/dp:text-slate-500" />
          <span
            className={`flex-1 truncate ${
              selectedDate ? 'text-slate-900' : 'text-slate-400'
            }`}
          >
            {selectedDate ? formatDisplay(selectedDate) : placeholder}
          </span>
          {clearable && selectedDate && !disabled ? (
            <span
              role="button"
              tabIndex={-1}
              aria-label="Limpiar fecha"
              onClick={clearValue}
              className="inline-flex h-6 w-6 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
            >
              <X className="h-3.5 w-3.5" />
            </span>
          ) : null}
        </button>

        {open ? (
          <div
            role="dialog"
            aria-label="Selector de fecha"
            className="animate-popover absolute left-0 z-50 mt-2 w-[300px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl ring-1 ring-black/5"
          >
            <div className="flex items-center justify-between gap-2 border-b border-slate-100 bg-slate-50/60 px-3 py-2.5">
              <button
                type="button"
                onClick={goPrevMonth}
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition-all duration-150 hover:bg-white hover:text-slate-900 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-200"
                aria-label="Mes anterior"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <p className="flex-1 text-center text-sm font-semibold capitalize text-slate-900">
                {monthLabel}
              </p>
              <button
                type="button"
                onClick={goNextMonth}
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition-all duration-150 hover:bg-white hover:text-slate-900 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-200"
                aria-label="Mes siguiente"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>

            <div className="px-3 pt-3">
              <div className="grid grid-cols-7 gap-1">
                {WEEKDAY_SHORT.map((day) => (
                  <div
                    key={day}
                    className="flex h-8 items-center justify-center text-[11px] font-semibold uppercase tracking-wide text-slate-400"
                  >
                    {day}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-1 pb-2">
                {cells.map(({ date, inMonth }, index) => {
                  const isToday = isSameDay(date, today);
                  const isSelected = selectedDate ? isSameDay(date, selectedDate) : false;
                  const disabledDay = isDisabledDay(date);

                  return (
                    <button
                      key={`${date.toISOString()}-${index}`}
                      type="button"
                      disabled={disabledDay}
                      onClick={() => pickDate(date)}
                      className={`relative flex h-9 w-9 items-center justify-center rounded-lg text-sm transition-all duration-150 ${
                        disabledDay
                          ? 'cursor-not-allowed text-slate-300'
                          : isSelected
                            ? 'bg-sky-600 font-semibold text-white shadow-sm hover:bg-sky-700'
                            : isToday
                              ? 'font-semibold text-sky-700 ring-1 ring-inset ring-sky-200 hover:bg-sky-50'
                              : inMonth
                                ? 'text-slate-700 hover:bg-slate-100'
                                : 'text-slate-300 hover:bg-slate-50'
                      } focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 focus-visible:ring-offset-1`}
                      aria-current={isToday ? 'date' : undefined}
                      aria-selected={isSelected || undefined}
                    >
                      {date.getDate()}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-between gap-2 border-t border-slate-100 bg-slate-50/60 px-3 py-2">
              <button
                type="button"
                onClick={jumpToToday}
                className="rounded-md px-2 py-1 text-xs font-semibold text-sky-700 transition-colors hover:bg-sky-50 hover:text-sky-800"
              >
                Hoy
              </button>
              {clearable && selectedDate ? (
                <button
                  type="button"
                  onClick={() => onChange('')}
                  className="rounded-md px-2 py-1 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800"
                >
                  Limpiar
                </button>
              ) : null}
            </div>
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
