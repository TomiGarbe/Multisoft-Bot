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
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto rounded-2xl">
        <table className="w-full min-w-max border-collapse divide-y divide-slate-200 text-left">
          <thead className="bg-slate-50">
            <tr>
              {headers.map((header) => (
                <th
                  key={header}
                  className="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          {hasRows ? (
            <tbody className="divide-y divide-slate-100 bg-white">{children}</tbody>
          ) : (
            <tbody>
              <tr>
                <td
                  colSpan={headers.length}
                  className="px-4 py-8 text-center text-sm text-slate-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            </tbody>
          )}
        </table>
      </div>
    </div>
  );
}
