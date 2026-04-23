'use client';

import type { ReactNode } from 'react';

interface TableProps {
  headers: string[];
  children: ReactNode;
  emptyMessage?: string;
  hasRows: boolean;
}

export default function Table({ headers, children, emptyMessage = 'No data available.', hasRows }: TableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              {headers.map((header) => (
                <th
                  key={header}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">{children}</tbody>
        </table>
      </div>

      {!hasRows ? <p className="px-4 py-8 text-center text-sm text-slate-500">{emptyMessage}</p> : null}
    </div>
  );
}
