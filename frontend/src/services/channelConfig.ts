import api from '@/services/api';
import type { ChannelBotConfig, ChannelConfigValidationStatus } from '@/types/channelConfig';

export async function getChannelConfig(configId: string): Promise<ChannelBotConfig> {
  const { data } = await api.get<ChannelBotConfig>(`/channel-config/${configId}`);
  return data;
}

export async function updateChannelConfig(
  configId: string,
  payload: {
    config_jsonb?: Record<string, unknown>;
    settings_jsonb?: Record<string, unknown>;
    user_types_jsonb?: Record<string, unknown>;
  },
): Promise<ChannelBotConfig> {
  const { data } = await api.put<ChannelBotConfig>(`/channel-config/${configId}`, payload);
  return data;
}

export async function getChannelConfigStatus(configId: string): Promise<ChannelConfigValidationStatus> {
  const { data } = await api.get<ChannelConfigValidationStatus>(`/channel-config/${configId}/status`);
  return data;
}
