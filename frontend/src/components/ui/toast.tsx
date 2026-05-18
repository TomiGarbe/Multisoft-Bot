'use client';

import { AlertTriangle, CheckCircle2, X } from 'lucide-react';
import { useCallback, useMemo, useState } from 'react';

export interface ToastItem {
  id: number;
  message: string;
  type: 'success' | 'error';
}

export function useToast() {
  const [items, setItems] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const pushToast = useCallback((message: string, type: 'success' | 'error') => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setItems((prev) => [...prev, { id, message, type }]);
    window.setTimeout(() => {
      setItems((prev) => prev.filter((item) => item.id !== id));
    }, 3500);
  }, []);

  return useMemo(
    () => ({
      items,
      success: (message: string) => pushToast(message, 'success'),
      error: (message: string) => pushToast(message, 'error'),
      remove: removeToast,
    }),
    [items, pushToast, removeToast],
  );
}

interface ToastViewportProps {
  toasts: ToastItem[];
  onClose: (id: number) => void;
}

export function ToastViewport({ toasts, onClose }: ToastViewportProps) {
  return (
    <div className="pointer-events-none fixed right-4 top-4 z-[2100] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((toast) => {
        const success = toast.type === 'success';
        return (
          <div
            key={toast.id}
            className={`animate-popover pointer-events-auto flex items-start gap-3 rounded-xl border px-3.5 py-3 text-sm shadow-lg ring-1 ring-black/5 ${
              success
                ? 'border-emerald-200 bg-white text-emerald-900'
                : 'border-rose-200 bg-white text-rose-900'
            }`}
          >
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                success ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'
              }`}
            >
              {success ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            </span>
            <p className="min-w-0 flex-1 leading-relaxed">{toast.message}</p>
            <button
              type="button"
              onClick={() => onClose(toast.id)}
              className="-mr-1 -mt-0.5 inline-flex h-6 w-6 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
              aria-label="Cerrar"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
