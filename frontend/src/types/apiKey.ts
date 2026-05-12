export interface ApiKeyItem {
  id: string;
  tenant_id: string;
  channel_id: string | null;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
}

export interface ApiKeyCreatePayload {
  tenant_id: string;
  channel_id?: string;
  name: string;
  expires_at?: string;
}

export interface ApiKeyCreatedItem extends ApiKeyItem {
  api_key: string;
}
