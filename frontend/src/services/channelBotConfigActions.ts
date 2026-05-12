import api from '@/services/api';
import type { IntegrationListItem } from '@/types/integration';

export async function getChannelBotConfigActions(channelBotConfigId: string): Promise<IntegrationListItem[]> {
  const { data } = await api.get<IntegrationListItem[]>(`/channel-bot-configs/${channelBotConfigId}/actions`);
  return data;
}

export async function replaceChannelBotConfigActions(channelBotConfigId: string, actionIds: string[]): Promise<IntegrationListItem[]> {
  const { data } = await api.put<IntegrationListItem[]>(`/channel-bot-configs/${channelBotConfigId}/actions`, {
    action_ids: actionIds,
  });
  return data;
}
