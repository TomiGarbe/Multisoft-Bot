import type { DashboardContactsByTypePoint } from '@/dashboard/types';

interface ContactsByTypeGridProps {
  items: DashboardContactsByTypePoint[];
}

export default function ContactsByTypeGrid({ items }: ContactsByTypeGridProps) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500">No hay datos suficientes.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <article key={item.key} className="rounded-xl border border-slate-200 bg-slate-50/40 p-4">
          <h3 className="text-sm font-semibold text-slate-900">{item.label}</h3>
          <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">Total</p>
          <p className="text-xl font-semibold text-slate-900">{item.total.toLocaleString('es-AR')}</p>
          <p className="mt-2 text-xs text-slate-500">Nuevos este mes</p>
          <p className="text-sm font-medium text-emerald-700">{item.newThisMonth.toLocaleString('es-AR')}</p>
        </article>
      ))}
    </div>
  );
}
