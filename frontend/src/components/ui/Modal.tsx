'use client';

import type { ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}

export default function Modal({ isOpen, title, onClose, children, footer }: ModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" onClick={onClose}>
      <div
        className="w-full max-w-3xl rounded-2xl border border-slate-200 bg-white shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close modal"
          >
            x
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto px-6 py-5">{children}</div>

        {footer ? <div className="border-t border-slate-200 px-6 py-4">{footer}</div> : null}
      </div>
    </div>
  );
}
