import api, { getActiveTenantContext } from './api';

export async function getUsageTotals(params?: { start_date?: string; end_date?: string }) {
  const { scope } = getActiveTenantContext();
  const { data } = await api.get('/analytics/usage/totals', {
    params: { ...params, scope },
  });
  return data;
}

export async function getUsageSeries(params?: {
  granularity?: 'day' | 'month';
  start_date?: string;
  end_date?: string;
}) {
  const { scope } = getActiveTenantContext();
  const { data } = await api.get('/analytics/usage/series', {
    params: { ...params, scope },
  });
  return data;
}
