import { getBusinessSummary, getUsageSeries } from '@/services/analytics';
import type {
  DashboardData,
  DashboardLoadOptions,
  DashboardSeriesPoint,
  DashboardTokenByTenantPoint,
} from '@/dashboard/types';

interface UsageSeriesResponse {
  series?: Array<{
    period_start?: string;
    request_count?: number;
    total_tokens?: number;
  }>;
}

function toDashboardSeries(series: UsageSeriesResponse['series']): DashboardSeriesPoint[] {
  return (series ?? []).map((point) => {
    const period = point.period_start ? new Date(point.period_start) : null;
    const label = period ? period.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' }) : 'N/A';
    return {
      label,
      requests: point.request_count ?? 0,
      tokens: point.total_tokens ?? 0,
    };
  });
}

function toTenantTokenDistribution(items: Array<{ tenant_id: string; tenant_name: string; total_tokens: number }>): DashboardTokenByTenantPoint[] {
  const total = items.reduce((acc, item) => acc + item.total_tokens, 0);
  return items.map((item) => ({
    tenantId: item.tenant_id,
    tenantName: item.tenant_name,
    totalTokens: item.total_tokens,
    percentage: total > 0 ? (item.total_tokens / total) * 100 : 0,
  }));
}

export async function loadDashboardData(options: DashboardLoadOptions): Promise<DashboardData> {
  const isGlobal = options.scope === 'global' && options.canUseGlobalScope;
  const notes: string[] = [];

  const [summary, usageSeries] = await Promise.all([
    getBusinessSummary({ scope: isGlobal ? 'global' : 'tenant' }),
    getUsageSeries({ granularity: 'day' }, { scope: isGlobal ? 'global' : 'tenant' }) as Promise<UsageSeriesResponse>,
  ]);

  if (summary.scope === 'global') {
    return {
      scope: 'global',
      contacts: {
        total: summary.contacts.total_contacts,
        newThisMonth: summary.contacts.new_contacts_this_month,
      },
      contactsByType: [],
      conversions: [],
      totalTokens: summary.tokens.total_tokens,
      tokensByChannel: [],
      tokensByTenant: toTenantTokenDistribution(summary.tokens.by_tenant),
      usageSeries: toDashboardSeries(usageSeries.series),
      notes,
    };
  }

  if (summary.conversions.flows.length === 0) {
    notes.push('No hay conversiones registradas por ahora.');
  }

  return {
    scope: 'tenant',
    contacts: {
      total: summary.contacts.total_contacts,
      newThisMonth: summary.contacts.new_contacts_this_month,
    },
    contactsByType: summary.contacts.by_type.map((item) => ({
      key: item.key,
      label: item.label,
      total: item.total,
      newThisMonth: item.new_this_month,
    })),
    conversions: summary.conversions.flows.map((item) => ({
      fromType: item.from_type,
      toType: item.to_type,
      count: item.count,
      rate: item.rate,
    })),
    totalTokens: summary.tokens.total_tokens,
    tokensByChannel: summary.tokens.by_channel.map((item) => ({
      channelId: item.channel_id,
      channelName: item.channel_name,
      totalTokens: item.total_tokens,
    })),
    tokensByTenant: [],
    usageSeries: toDashboardSeries(usageSeries.series),
    notes,
  };
}
