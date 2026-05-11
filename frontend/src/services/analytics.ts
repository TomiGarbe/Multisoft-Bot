import api from './api';

export type AnalyticsScope = 'tenant' | 'global';

export interface ContactTypeMetric {
  key: string;
  label: string;
  total: number;
  new_this_month: number;
}

export interface ConversionFlowMetric {
  from_type: string;
  to_type: string;
  count: number;
  rate: number;
}

export interface TokenByChannelMetric {
  channel_id: string;
  channel_name: string;
  total_tokens: number;
}

export interface TokenByTenantMetric {
  tenant_id: string;
  tenant_name: string;
  total_tokens: number;
}

export interface TenantBusinessSummaryResponse {
  scope: 'tenant';
  tenant_id: string;
  contacts: {
    total_contacts: number;
    new_contacts_this_month: number;
    by_type: ContactTypeMetric[];
    month_start: string;
  };
  tokens: {
    total_tokens: number;
    by_channel: TokenByChannelMetric[];
  };
  conversions: {
    flows: ConversionFlowMetric[];
  };
}

export interface GlobalBusinessSummaryResponse {
  scope: 'global';
  contacts: {
    total_contacts: number;
    new_contacts_this_month: number;
    by_type: ContactTypeMetric[];
    month_start: string;
  };
  tokens: {
    total_tokens: number;
    by_tenant: TokenByTenantMetric[];
  };
}

export async function getUsageTotals(
  params?: { start_date?: string; end_date?: string },
  options?: { scope?: AnalyticsScope },
) {
  const { data } = await api.get('/analytics/usage/totals', {
    params: { ...params, scope: options?.scope ?? 'tenant' },
  });
  return data;
}

export async function getUsageSeries(
  params?: {
    granularity?: 'day' | 'month';
    start_date?: string;
    end_date?: string;
  },
  options?: { scope?: AnalyticsScope },
) {
  const { data } = await api.get('/analytics/usage/series', {
    params: { ...params, scope: options?.scope ?? 'tenant' },
  });
  return data;
}

export async function getBusinessSummary(options?: { scope?: AnalyticsScope }) {
  const { data } = await api.get<TenantBusinessSummaryResponse | GlobalBusinessSummaryResponse>('/analytics/business/summary', {
    params: { scope: options?.scope ?? 'tenant' },
  });
  return data;
}
