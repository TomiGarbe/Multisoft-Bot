import type { DashboardTokenByTenantPoint } from '@/dashboard/types';

interface TenantTokenRankingProps {
  items: DashboardTokenByTenantPoint[];
}

export default function TenantTokenRanking({ items }: TenantTokenRankingProps) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500">No hay datos suficientes.</p>;
  }

  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.tenantId} className="space-y-1">
          <div className="flex items-center justify-between gap-3 text-sm">
            <span className="truncate font-medium text-slate-800">{item.tenantName}</span>
            <span className="text-slate-600">{item.totalTokens.toLocaleString('es-AR')} tokens</span>
          </div>
          <div className="h-2 rounded-full bg-slate-100">
            <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${Math.max(item.percentage, 4)}%` }} />
          </div>
          <p className="text-xs text-slate-500">{item.percentage.toFixed(1)}% del total</p>
        </li>
      ))}
    </ul>
  );
}
