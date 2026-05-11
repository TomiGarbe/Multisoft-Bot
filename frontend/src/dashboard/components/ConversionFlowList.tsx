import type { DashboardConversionPoint } from '@/dashboard/types';

interface ConversionFlowListProps {
  items: DashboardConversionPoint[];
}

export default function ConversionFlowList({ items }: ConversionFlowListProps) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500">No hay conversiones registradas.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
      {items.map((item) => (
        <article key={`${item.fromType}-${item.toType}`} className="rounded-xl border border-slate-200 bg-slate-50/40 p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-slate-900">
              {item.fromType} to {item.toType}
            </p>
            <p className="rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-semibold text-indigo-700">{item.rate.toFixed(1)}%</p>
          </div>
          <p className="mt-3 text-xs text-slate-500">Cantidad convertida</p>
          <p className="text-xl font-semibold text-slate-900">{item.count.toLocaleString('es-AR')}</p>
        </article>
      ))}
    </div>
  );
}
