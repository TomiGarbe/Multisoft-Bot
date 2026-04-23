'use client';

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
    <div className="pointer-events-none fixed right-4 top-4 z-[60] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto rounded-xl border px-4 py-3 text-sm shadow-lg ${
            toast.type === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border-rose-200 bg-rose-50 text-rose-800'
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <p>{toast.message}</p>
            <button
              type="button"
              onClick={() => onClose(toast.id)}
              className="text-xs font-semibold uppercase tracking-wide opacity-70 hover:opacity-100"
            >
              Close
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
