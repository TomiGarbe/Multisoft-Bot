import { useMemo, useState } from 'react';
import { Crown, TrendingUp, Users } from 'lucide-react';
import type { DashboardContactsByTypePoint } from '@/dashboard/types';

interface ContactsByTypeGridProps {
  items: DashboardContactsByTypePoint[];
}

function fallbackColor(key: string): string {
  const hash = key.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return `hsl(${hash % 360} 72% 46%)`;
}

export default function ContactsByTypeGrid({ items }: ContactsByTypeGridProps) {
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const segments = useMemo(() => {
    const total = items.reduce((acc, item) => acc + item.total, 0);
    return items
      .map((item) => ({
        ...item,
        percentage: total > 0 ? (item.total / total) * 100 : 0,
        color: item.color || fallbackColor(item.key),
      }))
      .filter((item) => item.total > 0)
      .sort((a, b) => b.total - a.total);
  }, [items]);

  if (items.length === 0 || segments.length === 0) {
    return <p className="text-sm text-slate-500">No hay datos suficientes.</p>;
  }

  return (
    <div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {segments.map((item, index) => {
          const isLeader = index === 0;
          const isActive = activeKey === item.key;
          const growth = item.total > 0 ? (item.newThisMonth / item.total) * 100 : 0;
          return (
            <article
              key={item.key}
              onPointerEnter={() => setActiveKey(item.key)}
              onPointerLeave={() => setActiveKey(null)}
              className={`group relative cursor-pointer overflow-hidden rounded-2xl border bg-white p-4 transition-all duration-200 ${
                isActive
                  ? 'border-transparent shadow-md -translate-y-0.5'
                  : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
              }`}
              style={{
                boxShadow: isActive ? `0 8px 22px -12px ${item.color}80` : undefined,
              }}
            >
              <span
                aria-hidden
                className="absolute inset-x-0 top-0 h-1 transition-opacity duration-200"
                style={{ backgroundColor: item.color, opacity: isActive ? 1 : 0.6 }}
              />
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg"
                      style={{
                        backgroundColor: `${item.color}1A`,
                        color: item.color,
                      }}
                    >
                      <Users className="h-3.5 w-3.5" />
                    </span>
                    <span className="truncate text-sm font-semibold text-slate-900">{item.label}</span>
                    {isLeader ? (
                      <span
                        className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide"
                        style={{ backgroundColor: `${item.color}1A`, color: item.color }}
                      >
                        <Crown className="h-2.5 w-2.5" />
                        Top
                      </span>
                    ) : null}
                  </div>
                </div>
                <span
                  className="rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset"
                  style={{
                    color: item.color,
                    borderColor: `${item.color}66`,
                    backgroundColor: `${item.color}1A`,
                  }}
                >
                  {item.percentage.toFixed(1)}%
                </span>
              </div>

              <div className="mt-4 flex items-end justify-between gap-3">
                <div>
                  <p className="text-2xl font-bold text-slate-900 tabular-nums">
                    {item.total.toLocaleString('es-AR')}
                  </p>
                  <p className="text-[11px] text-slate-500">contactos historicos</p>
                </div>
                <div className="text-right">
                  <p className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
                    <TrendingUp className="h-3 w-3" />+{item.newThisMonth.toLocaleString('es-AR')}
                  </p>
                  <p className="text-[10px] text-slate-400">
                    {growth.toFixed(1)}% nuevos este mes
                  </p>
                </div>
              </div>

              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${Math.max(item.percentage, 2)}%`,
                    backgroundColor: item.color,
                  }}
                />
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
