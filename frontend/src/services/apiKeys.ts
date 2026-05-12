import api from '@/services/api';
import type { ApiKeyCreatePayload, ApiKeyCreatedItem, ApiKeyItem } from '@/types/apiKey';

const BASE = '/api-keys';

export async function listApiKeys(): Promise<ApiKeyItem[]> {
  const { data } = await api.get<ApiKeyItem[]>(BASE);
  return data;
}

export async function createApiKey(payload: ApiKeyCreatePayload): Promise<ApiKeyCreatedItem> {
  const { data } = await api.post<ApiKeyCreatedItem>(BASE, payload);
  return data;
}

export async function revokeApiKey(apiKeyId: string): Promise<void> {
  await api.delete(`${BASE}/${apiKeyId}`);
}
