import { getBusinessSummary, getUsageSeries } from '@/services/analytics';
import { getChannelConfigBundle, getChannels } from '@/services/channels';
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
      date: point.period_start,
      requests: point.request_count ?? 0,
      tokens: point.total_tokens ?? 0,
    };
  });
}

async function resolveUserTypeColors(): Promise<Record<string, string>> {
  try {
    const channels = await getChannels();
    const entries = await Promise.all(
      channels
        .filter((channel) => channel.is_active)
        .map(async (channel) => {
          try {
            const bundle = await getChannelConfigBundle(channel.id);
            const types = bundle.user_types as { types?: Array<{ key?: string; color?: string }> };
            const pairs =
              types.types
                ?.filter((item) => typeof item?.key === 'string' && typeof item?.color === 'string')
                .map((item) => [String(item.key), String(item.color)] as const) ?? [];
            return pairs;
          } catch {
            return [];
          }
        }),
    );
    return Object.fromEntries(entries.flat());
  } catch {
    return {};
  }
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

  const [summary, usageSeries, typeColors] = await Promise.all([
    getBusinessSummary({ scope: isGlobal ? 'global' : 'tenant' }),
    getUsageSeries({ granularity: 'day' }, { scope: isGlobal ? 'global' : 'tenant' }) as Promise<UsageSeriesResponse>,
    resolveUserTypeColors(),
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
      color: typeColors[item.key],
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
