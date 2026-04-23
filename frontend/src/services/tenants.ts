import api from './api';
import type { Tenant, TenantCreate, TenantUpdate } from '@/types/tenant';

const BASE = '/tenants';

export async function getTenants(): Promise<Tenant[]> {
  const { data } = await api.get(BASE);
  return data;
}

export async function createTenant(payload: TenantCreate): Promise<Tenant> {
  const { data } = await api.post('/tenants', payload);
  return data;
}

export async function updateTenant(
  id: string,
  payload: TenantUpdate,
): Promise<Tenant> {
  const { data } = await api.put(`/tenants/${id}`, payload);
  return data;
}

export async function deleteTenant(id: string): Promise<void> {
  await api.delete(`${BASE}/${id}`);
}