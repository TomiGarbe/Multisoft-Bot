import type { DashboardTokenByChannelPoint } from '@/dashboard/types';

interface ChannelDistributionChartProps {
  data: DashboardTokenByChannelPoint[];
}

export default function ChannelDistributionChart({ data }: ChannelDistributionChartProps) {
  if (data.length === 0) {
    return <p className="text-sm text-slate-500">No hay canales conectados.</p>;
  }

  const total = data.reduce((sum, item) => sum + item.totalTokens, 0);

  return (
    <ul className="space-y-3">
      {data.map((item) => {
        const share = total > 0 ? (item.totalTokens / total) * 100 : 0;
        return (
          <li key={item.channelId} className="space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-600">
              <span className="truncate pr-2">{item.channelName}</span>
              <span>{item.totalTokens.toLocaleString('es-AR')} tokens</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${Math.max(share, 4)}%` }} />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
