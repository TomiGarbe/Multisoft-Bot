'use client';

import type { ReactNode } from 'react';

interface TableProps {
  headers: ReactNode[];
  children: ReactNode;
  emptyMessage?: ReactNode;
  hasRows: boolean;
  dense?: boolean;
}

export default function Table({
  headers,
  children,
  emptyMessage = 'Sin datos para mostrar.',
  hasRows,
  dense = false,
}: TableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="scrollbar-thin overflow-x-auto">
        <table className="w-full min-w-max border-collapse text-left">
          <thead className="bg-slate-50/80 backdrop-blur-sm">
            <tr className="border-b border-slate-200">
              {headers.map((header, index) => (
                <th
                  key={index}
                  className={`whitespace-nowrap ${
                    dense ? 'px-3 py-2.5' : 'px-4 py-3'
                  } text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500`}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          {hasRows ? (
            <tbody className="divide-y divide-slate-100 bg-white [&_tr]:transition-colors [&_tr]:duration-150 [&_tr:hover]:bg-slate-50/70">
              {children}
            </tbody>
          ) : (
            <tbody>
              <tr>
                <td
                  colSpan={headers.length}
                  className="px-4 py-12 text-center text-sm text-slate-500"
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
