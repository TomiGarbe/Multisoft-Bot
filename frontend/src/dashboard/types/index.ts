export type DashboardScope = 'tenant' | 'global';

export interface DashboardSeriesPoint {
  label: string;
  requests: number;
  tokens: number;
}

export interface DashboardContactOverview {
  total: number;
  newThisMonth: number;
}

export interface DashboardContactsByTypePoint {
  key: string;
  label: string;
  total: number;
  newThisMonth: number;
}

export interface DashboardConversionPoint {
  fromType: string;
  toType: string;
  count: number;
  rate: number;
}

export interface DashboardTokenByChannelPoint {
  channelId: string;
  channelName: string;
  totalTokens: number;
}

export interface DashboardTokenByTenantPoint {
  tenantId: string;
  tenantName: string;
  totalTokens: number;
  percentage: number;
}

export interface DashboardData {
  scope: DashboardScope;
  contacts: DashboardContactOverview;
  contactsByType: DashboardContactsByTypePoint[];
  conversions: DashboardConversionPoint[];
  totalTokens: number;
  tokensByChannel: DashboardTokenByChannelPoint[];
  tokensByTenant: DashboardTokenByTenantPoint[];
  usageSeries: DashboardSeriesPoint[];
  notes: string[];
}

export interface DashboardLoadOptions {
  scope: DashboardScope;
  canUseGlobalScope: boolean;
}
