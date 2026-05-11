import type { DashboardSeriesPoint } from '@/dashboard/types';

interface UsageSeriesChartProps {
  data: DashboardSeriesPoint[];
}

export default function UsageSeriesChart({ data }: UsageSeriesChartProps) {
  if (data.length === 0) {
    return <p className="text-sm text-slate-500">Sin datos en el periodo seleccionado.</p>;
  }

  const maxTokens = Math.max(...data.map((item) => item.tokens), 1);

  return (
    <div className="space-y-3">
      {data.map((item) => (
        <div key={item.label} className="space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-600">
            <span>{item.label}</span>
            <span>{item.tokens.toLocaleString('es-AR')} tokens</span>
          </div>
          <div className="h-2 rounded-full bg-slate-100">
            <div
              className="h-2 rounded-full bg-indigo-500"
              style={{ width: `${Math.max((item.tokens / maxTokens) * 100, 4)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
