import type { ChannelProviderId } from '@/constants/channelProviders';

export interface ChannelRuntimeConfig {
  provider?: ChannelProviderId;
  webhook_url?: string;
  connection_status?: 'connected' | 'disconnected' | 'error' | 'syncing' | 'pending' | string;
  last_sync_at?: string;
  [key: string]: unknown;
}

export interface Channel {
  id: string;
  tenant_id: string;
  type: string;
  name: string;
  external_id: string;
  config?: ChannelRuntimeConfig;
  is_active: boolean;
}

export interface ChannelCreate {
  tenant_id: string;
  type: string;
  name: string;
  external_id: string;
  config?: Record<string, unknown>;
  is_active: boolean;
}

export interface ChannelUpdate {
  type?: string;
  name?: string;
  external_id?: string;
  config?: Record<string, unknown>;
  is_active?: boolean;
}

