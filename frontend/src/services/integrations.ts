import api from '@/services/api';
import type {
  IntegrationItem,
  IntegrationListItem,
  IntegrationPayload,
  IntegrationTestResponse,
} from '@/types/integration';

export async function getIntegrations(): Promise<IntegrationListItem[]> {
  const { data } = await api.get<IntegrationListItem[]>('/bot-actions');
  return data;
}

export async function getIntegration(id: string): Promise<IntegrationItem> {
  const { data } = await api.get<IntegrationItem>(`/bot-actions/${id}`);
  return data;
}

export async function createIntegration(payload: IntegrationPayload): Promise<IntegrationItem> {
  const { data } = await api.post<IntegrationItem>('/bot-actions', payload);
  return data;
}

export async function updateIntegration(id: string, payload: Partial<IntegrationPayload>): Promise<IntegrationItem> {
  const { data } = await api.put<IntegrationItem>(`/bot-actions/${id}`, payload);
  return data;
}

export async function setIntegrationEnabled(id: string, enabled: boolean): Promise<IntegrationItem> {
  const { data } = await api.patch<IntegrationItem>(`/bot-actions/${id}/enabled`, { enabled });
  return data;
}

export async function deleteIntegration(id: string): Promise<void> {
  await api.delete(`/bot-actions/${id}`);
}

export async function testIntegration(id: string, variables: Record<string, unknown>): Promise<IntegrationTestResponse> {
  const { data } = await api.post<IntegrationTestResponse>(`/bot-actions/${id}/test`, { variables });
  return data;
}
