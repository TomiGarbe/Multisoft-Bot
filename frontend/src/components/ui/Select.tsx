'use client';

import { Check, ChevronDown } from 'lucide-react';
import {
  forwardRef,
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type ReactNode,
  type SelectHTMLAttributes,
} from 'react';

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
  icon?: ReactNode;
  disabled?: boolean;
}

interface SelectProps
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children' | 'size'> {
  label?: string;
  options: SelectOption[];
  placeholder?: string;
  error?: string;
  hint?: string;
  leadingIcon?: ReactNode;
  searchable?: boolean;
  size?: 'sm' | 'md';
}

function fireNativeChange(select: HTMLSelectElement, value: string) {
  const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set;
  if (setter) setter.call(select, value);
  else select.value = value;
  select.dispatchEvent(new Event('change', { bubbles: true }));
}

const SIZE_STYLES = {
  sm: 'h-9 text-sm',
  md: 'h-10 text-sm',
};

const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  {
    label,
    id,
    options,
    placeholder,
    error,
    hint,
    leadingIcon,
    searchable = false,
    className = '',
    disabled,
    value,
    defaultValue,
    onChange,
    required,
    name,
    size = 'md',
    ...nativeProps
  },
  forwardedRef,
) {
  const reactId = useId();
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : `sel-${reactId}`);
  const buttonId = `${selectId}-trigger`;

  const innerSelectRef = useRef<HTMLSelectElement | null>(null);
  const setRefs = useCallback(
    (node: HTMLSelectElement | null) => {
      innerSelectRef.current = node;
      if (typeof forwardedRef === 'function') forwardedRef(node);
      else if (forwardedRef) {
        (forwardedRef as React.MutableRefObject<HTMLSelectElement | null>).current = node;
      }
    },
    [forwardedRef],
  );

  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState<number>(-1);

  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = useState<string>(
    typeof defaultValue === 'string' ? defaultValue : '',
  );
  const currentValue = isControlled ? String(value ?? '') : internalValue;

  const optionsWithPlaceholder = useMemo(() => {
    const list = options.map((opt) => ({ ...opt, value: String(opt.value) }));
    if (placeholder) return [{ value: '', label: placeholder, disabled: required }, ...list];
    return list;
  }, [options, placeholder, required]);

  const filteredOptions = useMemo(() => {
    if (!searchable || !search.trim()) return optionsWithPlaceholder;
    const q = search.trim().toLowerCase();
    return optionsWithPlaceholder.filter((opt) =>
      `${opt.label} ${opt.description ?? ''}`.toLowerCase().includes(q),
    );
  }, [optionsWithPlaceholder, searchable, search]);

  const selectedOption = optionsWithPlaceholder.find((opt) => opt.value === currentValue) ?? null;

  useEffect(() => {
    if (!open) {
      setSearch('');
      setActiveIndex(-1);
      return;
    }
    const handler = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const currentIndex = filteredOptions.findIndex((opt) => opt.value === currentValue);
    setActiveIndex(currentIndex >= 0 ? currentIndex : 0);
  }, [open, currentValue, filteredOptions]);

  const commitValue = (next: string) => {
    if (!isControlled) setInternalValue(next);
    if (innerSelectRef.current && onChange) {
      fireNativeChange(innerSelectRef.current, next);
    }
  };

  const pickOption = (option: SelectOption) => {
    if (option.disabled) return;
    commitValue(option.value);
    setOpen(false);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return;

    if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (!open) setOpen(true);
    }

    if (open) {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setActiveIndex((idx) => Math.min(idx + 1, filteredOptions.length - 1));
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setActiveIndex((idx) => Math.max(idx - 1, 0));
      } else if (event.key === 'Enter') {
        event.preventDefault();
        const opt = filteredOptions[activeIndex];
        if (opt) pickOption(opt);
      } else if (event.key === 'Escape') {
        event.preventDefault();
        setOpen(false);
      }
    }
  };

  return (
    <div className="space-y-1.5" ref={containerRef}>
      {label ? (
        <label htmlFor={buttonId} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      ) : null}

      <select
        ref={setRefs}
        id={selectId}
        name={name}
        value={currentValue}
        onChange={(event: ChangeEvent<HTMLSelectElement>) => {
          if (!isControlled) setInternalValue(event.target.value);
          onChange?.(event);
        }}
        disabled={disabled}
        required={required}
        tabIndex={-1}
        aria-hidden
        className="sr-only"
        {...nativeProps}
      >
        {optionsWithPlaceholder.map((opt) => (
          <option key={opt.value || '__placeholder__'} value={opt.value} disabled={opt.disabled}>
            {opt.label}
          </option>
        ))}
      </select>

      <div className="relative">
        <button
          id={buttonId}
          type="button"
          disabled={disabled}
          onClick={() => setOpen((v) => !v)}
          onKeyDown={handleKeyDown}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={`${selectId}-listbox`}
          className={`group/select flex w-full items-center gap-2 rounded-xl border bg-white px-3.5 text-left outline-none transition-all duration-150 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 ${
            SIZE_STYLES[size]
          } ${
            error
              ? 'border-rose-400 hover:border-rose-500 focus-visible:border-rose-500 focus-visible:ring-2 focus-visible:ring-rose-200'
              : open
                ? 'border-sky-500 ring-2 ring-sky-200'
                : 'border-slate-300 hover:border-slate-400 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-200'
          } ${className}`.trim()}
        >
          {leadingIcon ? (
            <span className="text-slate-400 [&_svg]:h-4 [&_svg]:w-4">{leadingIcon}</span>
          ) : selectedOption?.icon ? (
            <span className="text-slate-500 [&_svg]:h-4 [&_svg]:w-4">{selectedOption.icon}</span>
          ) : null}
          <span
            className={`flex-1 truncate ${
              selectedOption && selectedOption.value !== ''
                ? 'text-slate-900'
                : 'text-slate-400'
            }`}
          >
            {selectedOption?.label ?? placeholder ?? ' '}
          </span>
          <ChevronDown
            className={`h-4 w-4 shrink-0 text-slate-400 transition-transform duration-150 ${
              open ? 'rotate-180 text-sky-500' : ''
            }`}
          />
        </button>

        {open ? (
          <div className="animate-popover absolute left-0 right-0 z-50 mt-2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg ring-1 ring-black/5">
            {searchable ? (
              <div className="border-b border-slate-100 p-2">
                <input
                  autoFocus
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar..."
                  className="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-sm outline-none placeholder:text-slate-400 focus:border-sky-400 focus:bg-white"
                />
              </div>
            ) : null}
            <ul
              ref={listRef}
              id={`${selectId}-listbox`}
              role="listbox"
              className="scrollbar-thin max-h-64 overflow-y-auto py-1"
            >
              {filteredOptions.length === 0 ? (
                <li className="px-3 py-4 text-center text-xs text-slate-500">Sin resultados</li>
              ) : (
                filteredOptions.map((option, index) => {
                  const isSelected = option.value === currentValue;
                  const isActive = index === activeIndex;
                  return (
                    <li key={option.value || '__placeholder__'}>
                      <button
                        type="button"
                        role="option"
                        aria-selected={isSelected}
                        disabled={option.disabled}
                        onMouseEnter={() => setActiveIndex(index)}
                        onClick={() => pickOption(option)}
                        className={`flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm transition-colors ${
                          option.disabled
                            ? 'cursor-not-allowed text-slate-400'
                            : isSelected
                              ? 'bg-sky-50/70 text-sky-900'
                              : isActive
                                ? 'bg-slate-100 text-slate-900'
                                : 'text-slate-700'
                        }`}
                      >
                        {option.icon ? (
                          <span
                            className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                              isSelected ? 'bg-sky-100 text-sky-600' : 'bg-slate-100 text-slate-500'
                            }`}
                          >
                            {option.icon}
                          </span>
                        ) : null}
                        <span className="min-w-0 flex-1">
                          <span className="block truncate font-medium">{option.label}</span>
                          {option.description ? (
                            <span className="block truncate text-xs text-slate-500">
                              {option.description}
                            </span>
                          ) : null}
                        </span>
                        {isSelected ? (
                          <Check className="h-4 w-4 shrink-0 text-sky-600" strokeWidth={3} />
                        ) : null}
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
});

export default Select;
